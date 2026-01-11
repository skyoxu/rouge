using System;
using System.Collections;
using System.Linq;
using System.Reflection;
using System.Runtime.ExceptionServices;
using Xunit;

namespace Game.Core.Tests.State;

public sealed class GameStateRunSeedTests
{
    // References: ADR-0021-csharp-domain-layer-architecture, ADR-0024-godot-test-strategy

    // ACC:T10.2
    [Fact]
    public void GameState_exposes_RunSeed_as_int_and_in_primary_constructor()
    {
        var gameStateType = GetGameCoreType("Game.Core.Domain.GameState");

        var prop = gameStateType.GetProperty("RunSeed", BindingFlags.Instance | BindingFlags.Public);
        Assert.NotNull(prop);
        Assert.Equal(typeof(int), prop!.PropertyType);

        var hasCtorParam = gameStateType
            .GetConstructors(BindingFlags.Instance | BindingFlags.Public)
            .SelectMany(c => c.GetParameters())
            .Any(p =>
                string.Equals(p.Name, "RunSeed", StringComparison.OrdinalIgnoreCase)
                && p.ParameterType == typeof(int));

        Assert.True(hasCtorParam, "GameState primary constructor must include RunSeed:int for persistence/replay.");
    }

    [Fact]
    public void Engine_startup_seeds_rng_with_GameState_RunSeed()
    {
        var rngInterfaceType = GetGameCoreType("Game.Core.Services.IRngService");

        var proxy = CreateDispatchProxy(rngInterfaceType, typeof(RngSpyProxy));
        var spy = (RngSpyProxy)proxy;

        var engine = CreateGameEngineCoreWithRng(proxy, rngInterfaceType);

        var state = GetPropertyValue(engine, "State");
        Assert.NotNull(state);

        int runSeed = GetIntProperty(state!, "RunSeed");

        InvokeVoid(engine, "Start");

        Assert.True(spy.SetSeedCallCount >= 1, "Expected engine startup to call IRngService.SetSeed(runSeed).");
        Assert.Equal(runSeed, spy.LastSeed);
    }

    private static Assembly GameCoreAssembly => Assembly.Load("Game.Core");

    private static Type GetGameCoreType(string fullName)
    {
        var t = GameCoreAssembly.GetType(fullName, throwOnError: false, ignoreCase: false);
        Assert.NotNull(t);
        return t!;
    }

    private static object CreateDispatchProxy(Type interfaceType, Type proxyType)
    {
        var create = typeof(DispatchProxy)
            .GetMethods(BindingFlags.Public | BindingFlags.Static)
            .FirstOrDefault(m => string.Equals(m.Name, "Create", StringComparison.Ordinal) && m.IsGenericMethodDefinition);

        Assert.NotNull(create);

        var closed = create!.MakeGenericMethod(interfaceType, proxyType);
        var raw = closed.Invoke(null, null);
        Assert.NotNull(raw);
        return raw!;
    }

    private static object CreateGameEngineCoreWithRng(object rngProxy, Type rngInterfaceType)
    {
        var engineType = GetGameCoreType("Game.Core.Engine.GameEngineCore");
        var config = CreateGameConfig();
        var inventory = CreateInventory();

        var ctors = engineType.GetConstructors(BindingFlags.Instance | BindingFlags.Public)
            .Where(c => c.GetParameters().Any(p => p.ParameterType == rngInterfaceType))
            .ToArray();

        Assert.True(ctors.Length >= 1, "GameEngineCore must accept IRngService for deterministic runs.");

        foreach (var ctor in ctors)
        {
            var ps = ctor.GetParameters();
            var args = new object?[ps.Length];
            bool ok = true;

            for (int i = 0; i < ps.Length; i++)
            {
                var p = ps[i];

                if (p.ParameterType.IsInstanceOfType(config))
                {
                    args[i] = config;
                    continue;
                }

                if (p.ParameterType.IsInstanceOfType(inventory))
                {
                    args[i] = inventory;
                    continue;
                }

                if (p.ParameterType == rngInterfaceType)
                {
                    args[i] = rngProxy;
                    continue;
                }

                if (!p.ParameterType.IsValueType)
                {
                    args[i] = null;
                    continue;
                }

                if (p.HasDefaultValue)
                {
                    args[i] = p.DefaultValue;
                    continue;
                }

                ok = false;
                break;
            }

            if (!ok) continue;

            var instance = ctor.Invoke(args);
            Assert.NotNull(instance);
            return instance!;
        }

        Assert.Fail("Could not construct GameEngineCore with an IRngService parameter.");
        return null!;
    }

    private static object CreateGameConfig()
    {
        var configType = GetGameCoreType("Game.Core.Domain.GameConfig");
        var difficultyType = GetGameCoreType("Game.Core.Domain.Difficulty");
        var medium = Enum.Parse(difficultyType, "Medium", ignoreCase: false);

        var cfg = Activator.CreateInstance(
            configType,
            new object?[]
            {
                50,
                100,
                1.0,
                false,
                medium
            }
        );

        Assert.NotNull(cfg);
        return cfg!;
    }

    private static object CreateInventory()
    {
        var invType = GetGameCoreType("Game.Core.Domain.Inventory");
        var inv = Activator.CreateInstance(invType);
        Assert.NotNull(inv);
        return inv!;
    }

    private static object? GetPropertyValue(object instance, string propertyName)
    {
        var t = instance.GetType();
        var pi = t.GetProperty(propertyName, BindingFlags.Instance | BindingFlags.Public);
        Assert.NotNull(pi);
        return pi!.GetValue(instance);
    }

    private static int GetIntProperty(object instance, string propertyName)
    {
        var t = instance.GetType();
        var pi = t.GetProperty(propertyName, BindingFlags.Instance | BindingFlags.Public);
        Assert.NotNull(pi);
        Assert.Equal(typeof(int), pi!.PropertyType);
        return (int)pi.GetValue(instance)!;
    }

    private static void InvokeVoid(object instance, string methodName, params object?[] args)
    {
        var t = instance.GetType();
        var mi = t.GetMethod(methodName, BindingFlags.Instance | BindingFlags.Public);
        Assert.NotNull(mi);

        try
        {
            mi!.Invoke(instance, args);
        }
        catch (TargetInvocationException ex) when (ex.InnerException is not null)
        {
            ExceptionDispatchInfo.Capture(ex.InnerException).Throw();
            throw;
        }
    }

    private class RngSpyProxy : DispatchProxy
    {
        public int SetSeedCallCount { get; private set; }
        public int LastSeed { get; private set; } = int.MinValue;

        protected override object? Invoke(MethodInfo? targetMethod, object?[]? args)
        {
            if (targetMethod is null) throw new InvalidOperationException("DispatchProxy invoked with null targetMethod.");

            args ??= Array.Empty<object?>();

            if (string.Equals(targetMethod.Name, "SetSeed", StringComparison.Ordinal))
            {
                SetSeedCallCount++;
                LastSeed = (int)(args[0] ?? throw new ArgumentNullException(nameof(args), "SetSeed(seed) seed was null."));
                return null;
            }

            if (string.Equals(targetMethod.Name, "NextInt", StringComparison.Ordinal))
            {
                return (int)(args[0] ?? 0);
            }

            if (string.Equals(targetMethod.Name, "NextFloat", StringComparison.Ordinal))
            {
                return 0f;
            }

            if (string.Equals(targetMethod.Name, "Shuffle", StringComparison.Ordinal))
            {
                return null;
            }

            if (string.Equals(targetMethod.Name, "PickRandom", StringComparison.Ordinal))
            {
                if (args.Length != 1) throw new ArgumentException("PickRandom expected exactly one argument.");
                if (args[0] is null) throw new ArgumentNullException("list");
                if (args[0] is not IList list) throw new ArgumentException("PickRandom expected a List<T>.");
                if (list.Count == 0) throw new ArgumentException("PickRandom expected a non-empty list.");
                return list[0];
            }

            throw new NotSupportedException($"Unexpected IRngService call: {targetMethod.Name}");
        }
    }
}
