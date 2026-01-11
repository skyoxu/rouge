using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using Xunit;

namespace Game.Core.Tests.Services;

public class RngServiceTests
{
    [Fact]
    // ACC:T10.2
    public void RngService_has_expected_contract_and_field_layout()
    {
        var rngServiceType = GetGameCoreType("Game.Core.Services.RngService");
        var rngInterfaceType = GetGameCoreType("Game.Core.Services.IRngService");

        Assert.True(rngInterfaceType.IsInterface, "IRngService must be an interface.");
        Assert.True(rngInterfaceType.IsAssignableFrom(rngServiceType), "RngService must implement IRngService.");

        var field = rngServiceType.GetField("_rng", BindingFlags.Instance | BindingFlags.NonPublic);
        Assert.NotNull(field);
        Assert.Equal(typeof(Random), field!.FieldType);
    }

    [Fact]
    public void SetSeed_reseeds_and_repeats_sequence_for_NextInt()
    {
        var svc = CreateRngService();
        InvokeVoid(svc, "SetSeed", 123);

        var first = Enumerable.Range(0, 8).Select(_ => InvokeNextInt(svc, 0, 100)).ToArray();

        InvokeVoid(svc, "SetSeed", 123);
        var second = Enumerable.Range(0, 8).Select(_ => InvokeNextInt(svc, 0, 100)).ToArray();

        Assert.Equal(first, second);
    }

    [Fact]
    public void NextInt_returns_values_in_expected_range()
    {
        var svc = CreateRngService();
        InvokeVoid(svc, "SetSeed", 7);

        for (int i = 0; i < 200; i++)
        {
            int v = InvokeNextInt(svc, -2, 3);
            Assert.True(v >= -2, "NextInt must be inclusive of min.");
            Assert.True(v < 3, "NextInt must be exclusive of max.");
        }
    }

    [Fact]
    public void NextFloat_returns_values_in_expected_range()
    {
        var svc = CreateRngService();
        InvokeVoid(svc, "SetSeed", 99);

        for (int i = 0; i < 200; i++)
        {
            object raw = Invoke(svc, "NextFloat");
            Assert.True(raw is float, "NextFloat must return System.Single (float).");
            float v = (float)raw;
            Assert.True(v >= 0f, "NextFloat must be inclusive of 0.");
            Assert.True(v < 1f, "NextFloat must be exclusive of 1.");
        }
    }

    [Fact]
    public void Shuffle_is_deterministic_for_a_fixed_seed_and_preserves_elements()
    {
        var svc1 = CreateRngService();
        var svc2 = CreateRngService();

        InvokeVoid(svc1, "SetSeed", 42);
        InvokeVoid(svc2, "SetSeed", 42);

        var a = new List<int> { 1, 2, 3, 4, 5, 6, 7, 8 };
        var b = new List<int> { 1, 2, 3, 4, 5, 6, 7, 8 };

        InvokeShuffle(svc1, a);
        InvokeShuffle(svc2, b);

        Assert.Equal(a, b);
        Assert.Equal(new[] { 1, 2, 3, 4, 5, 6, 7, 8 }, a.OrderBy(x => x).ToArray());
    }

    [Fact]
    public void PickRandom_returns_an_element_from_the_list_and_is_deterministic_for_seed()
    {
        var svc1 = CreateRngService();
        var svc2 = CreateRngService();

        InvokeVoid(svc1, "SetSeed", 555);
        InvokeVoid(svc2, "SetSeed", 555);

        var list1 = new List<string> { "a", "b", "c", "d" };
        var list2 = new List<string> { "a", "b", "c", "d" };

        var p1 = InvokePickRandom<string>(svc1, list1);
        var p2 = InvokePickRandom<string>(svc2, list2);

        Assert.Contains(p1, list1);
        Assert.Equal(p1, p2);
        Assert.Equal(4, list1.Count);
    }

    private static Type GetGameCoreType(string fullName)
    {
        var asm = Assembly.Load("Game.Core");
        var t = asm.GetType(fullName, throwOnError: false, ignoreCase: false);
        Assert.NotNull(t);
        return t!;
    }

    private static object CreateRngService()
    {
        var t = GetGameCoreType("Game.Core.Services.RngService");
        var obj = Activator.CreateInstance(t);
        Assert.NotNull(obj);
        return obj!;
    }

    private static object Invoke(object instance, string methodName, params object[] args)
    {
        var t = instance.GetType();
        var mi = t.GetMethod(methodName, BindingFlags.Instance | BindingFlags.Public);
        Assert.NotNull(mi);
        return mi!.Invoke(instance, args) ?? throw new InvalidOperationException($"{t.FullName}.{methodName} returned null.");
    }

    private static void InvokeVoid(object instance, string methodName, params object[] args)
    {
        var t = instance.GetType();
        var mi = t.GetMethod(methodName, BindingFlags.Instance | BindingFlags.Public);
        Assert.NotNull(mi);
        mi!.Invoke(instance, args);
    }

    private static int InvokeNextInt(object instance, int min, int max)
    {
        object raw = Invoke(instance, "NextInt", min, max);
        Assert.True(raw is int, "NextInt must return int.");
        return (int)raw;
    }

    private static void InvokeShuffle<T>(object instance, List<T> list)
    {
        var t = instance.GetType();
        var mi = FindGenericListMethod(t, "Shuffle", genericArgCount: 1);
        var closed = mi.MakeGenericMethod(typeof(T));
        closed.Invoke(instance, new object[] { list });
    }

    private static T InvokePickRandom<T>(object instance, List<T> list)
    {
        var t = instance.GetType();
        var mi = FindGenericListMethod(t, "PickRandom", genericArgCount: 1);
        var closed = mi.MakeGenericMethod(typeof(T));
        object? raw = closed.Invoke(instance, new object[] { list });
        Assert.NotNull(raw);
        Assert.True(raw is T, "PickRandom must return T.");
        return (T)raw;
    }

    private static MethodInfo FindGenericListMethod(Type serviceType, string methodName, int genericArgCount)
    {
        var methods = serviceType.GetMethods(BindingFlags.Instance | BindingFlags.Public)
            .Where(m => string.Equals(m.Name, methodName, StringComparison.Ordinal))
            .Where(m => m.IsGenericMethodDefinition)
            .Where(m => m.GetGenericArguments().Length == genericArgCount)
            .Where(m => m.GetParameters().Length == 1)
            .ToArray();

        foreach (var m in methods)
        {
            var p = m.GetParameters()[0].ParameterType;
            if (p.IsGenericType && p.GetGenericTypeDefinition() == typeof(List<>)) return m;
        }

        throw new InvalidOperationException($"Could not locate method {serviceType.FullName}.{methodName}<T>(List<T>)." );
    }
}
