using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Reflection;
using System.Threading.Tasks;
using Game.Core.Contracts;
using Game.Core.Domain;
using Game.Core.Services;
using Xunit;

namespace Game.Core.Tests.Domain.CardPile
{
    public sealed class CardPilePerfRegressionTests
    {
        [Fact(DisplayName = "ACC:T2.2 CardPile perf-regression precondition: required public surface exists")]
        public void ACC_T2_2_CardPile_required_public_surface_is_present()
        {
            var cardPileType = FindTypeByFullName("Game.Core.Domain.CardPile");
            Assert.NotNull(cardPileType);

            Assert.True(cardPileType!.IsClass, "CardPile must be a class.");
            Assert.True(cardPileType.IsPublic, "CardPile must be public.");
            Assert.False(cardPileType.IsAbstract, "CardPile must not be abstract.");

            AssertHasInstanceMethod(cardPileType, "Draw", new[] { typeof(int) });
            AssertHasInstanceMethodWithSingleParameter(cardPileType, "Discard");
            AssertHasInstanceMethodWithSingleParameter(cardPileType, "Exhaust");
            AssertHasInstanceMethod(cardPileType, "Shuffle", Type.EmptyTypes);
            AssertHasInstanceMethodWithSingleParameter(cardPileType, "AddCard");
            AssertHasInstanceMethodWithSingleParameter(cardPileType, "RemoveCard");
            AssertHasInstanceMethodWithSingleParameter(cardPileType, "UpgradeCard");

            var cardDrawn = FindTypeInAssembly(assemblyName: "Game.Core", fullName: "Game.Core.Contracts.Rouge.Cards.CardDrawn");
            Assert.NotNull(cardDrawn);

            var cardDiscarded = FindTypeInAssembly(assemblyName: "Game.Core", fullName: "Game.Core.Contracts.Rouge.Cards.CardDiscarded");
            Assert.NotNull(cardDiscarded);
        }

        [Fact(DisplayName = "ACC:T2.2 CardPile perf-regression: 100+ draw scenario stays responsive and preserves event order")]
        public void ACC_T2_2_draw_120_with_reshuffle_is_reasonably_fast_and_orders_events()
        {
            var rng = new RngService();
            rng.SetSeed(123);

            var bus = new CapturingEventBus();
            var sut = new Game.Core.Domain.CardPile(rng, bus);

            // 60 cards: first Draw(60) drains DrawPile, then Discard(60) fills DiscardPile,
            // then Draw(60) forces reshuffle DiscardPile -> DrawPile.
            for (var i = 0; i < 60; i++)
            {
                sut.AddCard(CreateCardDefinition($"card_{i}"));
            }

            var sw = Stopwatch.StartNew();

            for (var i = 0; i < 60; i++)
            {
                sut.Draw(1);
                var id = sut.Hand.Single().Id;
                sut.Discard(id);
            }

            for (var i = 0; i < 60; i++)
            {
                sut.Draw(1);
                var id = sut.Hand.Single().Id;
                sut.Discard(id);
            }

            sw.Stop();

            Assert.Empty(sut.Hand);
            Assert.Empty(sut.DrawPile);
            Assert.Equal(60, sut.DiscardPile.Count);

            var drawn = bus.Events.Where(e => e.Type == "core.card.drawn").ToList();
            Assert.Equal(120, drawn.Count);

            // Loose time budget to catch catastrophic slowdowns (e.g., accidental O(n^2)).
            Assert.True(sw.ElapsedMilliseconds < 3000, $"Draw/discard/reshuffle scenario took too long: {sw.ElapsedMilliseconds}ms");

            var drawOrders = drawn.Select(ReadDrawOrder).ToList();
            Assert.Equal(120, drawOrders.Count);
            Assert.Equal(Enumerable.Range(1, 120).ToArray(), drawOrders.ToArray());
        }

        private static void AssertHasInstanceMethod(Type type, string name, Type[] parameterTypes)
        {
            var method = type.GetMethod(
                name,
                BindingFlags.Instance | BindingFlags.Public,
                binder: null,
                types: parameterTypes,
                modifiers: null);

            Assert.True(method != null, $"Missing public instance method: {type.FullName}.{name}({string.Join(", ", parameterTypes.Select(t => t.Name))})");
        }

        private static void AssertHasInstanceMethodWithSingleParameter(Type type, string name)
        {
            var candidates = type
                .GetMethods(BindingFlags.Instance | BindingFlags.Public)
                .Where(m => string.Equals(m.Name, name, StringComparison.Ordinal))
                .Where(m => m.GetParameters().Length == 1)
                .ToArray();

            Assert.True(candidates.Length > 0, $"Missing public instance method with one parameter: {type.FullName}.{name}(...) ");
        }

        private static Type? FindTypeByFullName(string fullName)
        {
            foreach (var assembly in AppDomain.CurrentDomain.GetAssemblies())
            {
                var type = assembly.GetType(fullName, throwOnError: false, ignoreCase: false);
                if (type != null)
                {
                    return type;
                }
            }

            return null;
        }

        private static Type? FindTypeInAssembly(string assemblyName, string fullName)
        {
            Assembly? target = null;
            foreach (var asm in AppDomain.CurrentDomain.GetAssemblies())
            {
                if (!string.Equals(asm.GetName().Name, assemblyName, StringComparison.Ordinal)) continue;
                target = asm;
                break;
            }

            if (target is null)
            {
                try
                {
                    target = Assembly.Load(assemblyName);
                }
                catch
                {
                    return null;
                }
            }

            return target.GetType(fullName, throwOnError: false, ignoreCase: false);
        }

        private static CardDefinition CreateCardDefinition(string id)
        {
            return CardDefinition.CreateOrThrow(
                id: id,
                name: id,
                type: CardType.Attack,
                cost: 1,
                targetRule: TargetRule.SingleEnemy,
                effectCommands: Array.Empty<Game.Core.Contracts.Rouge.Effects.EffectCommand>(),
                textKey: id,
                rarity: "common",
                classTag: "test"
            );
        }

        private static int ReadDrawOrder(DomainEvent evt)
        {
            using var doc = System.Text.Json.JsonDocument.Parse(evt.DataJson);
            var root = doc.RootElement;
            var order = root.GetProperty("DrawOrder").GetInt32();
            return order;
        }

        private sealed class CapturingEventBus : IEventBus
        {
            public List<DomainEvent> Events { get; } = new();

            public Task PublishAsync(DomainEvent evt)
            {
                Events.Add(evt);
                return Task.CompletedTask;
            }

            public IDisposable Subscribe(Func<DomainEvent, Task> handler) => throw new NotSupportedException();
        }
    }
}
