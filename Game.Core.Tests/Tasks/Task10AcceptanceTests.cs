using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using System.Runtime.ExceptionServices;
using Xunit;

namespace Game.Core.Tests.Tasks;

public class Task10AcceptanceTests
{
    [Fact]
    public void RngService_exposes_expected_public_contract()
    {
        var rngServiceType = GetGameCoreType("Game.Core.Services.RngService");
        var rngInterfaceType = GetGameCoreType("Game.Core.Services.IRngService");

        Assert.True(rngInterfaceType.IsInterface, "IRngService must be an interface.");
        Assert.True(rngInterfaceType.IsPublic, "IRngService must be public.");
        Assert.True(rngInterfaceType.IsAssignableFrom(rngServiceType), "RngService must implement IRngService.");

        AssertHasMethod(rngInterfaceType, "SetSeed", typeof(void), typeof(int));
        AssertHasMethod(rngInterfaceType, "NextInt", typeof(int), typeof(int), typeof(int));
        AssertHasMethod(rngInterfaceType, "NextFloat", typeof(float));

        AssertHasGenericListMethod(rngInterfaceType, "Shuffle");
        AssertHasGenericListMethod(rngInterfaceType, "PickRandom");

        var field = rngServiceType.GetField("_rng", BindingFlags.Instance | BindingFlags.NonPublic);
        Assert.NotNull(field);
        Assert.Equal(typeof(Random), field!.FieldType);
    }

    [Fact]
    public void SetSeed_makes_sequences_repeatable_across_rng_operations()
    {
        // ACC:T10.1 ACC:T10.3
        var svc = CreateRngService();

        InvokeVoid(svc, "SetSeed", 123);
        var run1 = CaptureRun(svc);

        InvokeVoid(svc, "SetSeed", 123);
        var run2 = CaptureRun(svc);

        Assert.Equal(run1.Ints, run2.Ints);
        Assert.Equal(run1.FloatBits, run2.FloatBits);
        Assert.Equal(run1.Shuffled, run2.Shuffled);
        Assert.Equal(run1.Picked, run2.Picked);

        var expectedElements = new[] { 1, 2, 3, 4, 5, 6, 7, 8 };
        Assert.Equal(expectedElements, run1.Shuffled.OrderBy(x => x).ToArray());
    }

    [Fact]
    public void RngService_throws_on_invalid_arguments()
    {
        var svc = CreateRngService();
        InvokeVoid(svc, "SetSeed", 1);

        Assert.Throws<ArgumentOutOfRangeException>(() => Invoke<int>(svc, "NextInt", 10, 5));

        Assert.Throws<ArgumentNullException>(() => InvokeShuffle<int>(svc, null));
        Assert.ThrowsAny<ArgumentException>(() => InvokePickRandom<int>(svc, null));
        Assert.ThrowsAny<ArgumentException>(() => InvokePickRandom<int>(svc, new List<int>()));
    }

    private sealed record RunSnapshot(int[] Ints, int[] FloatBits, List<int> Shuffled, string Picked);

    private static RunSnapshot CaptureRun(object svc)
    {
        var ints = Enumerable.Range(0, 12).Select(_ => Invoke<int>(svc, "NextInt", 0, 1_000_000)).ToArray();
        var floatBits = Enumerable.Range(0, 12)
            .Select(_ => BitConverter.SingleToInt32Bits(Invoke<float>(svc, "NextFloat")))
            .ToArray();

        var list = new List<int> { 1, 2, 3, 4, 5, 6, 7, 8 };
        InvokeShuffle(svc, list);

        var pickList = new List<string> { "a", "b", "c", "d" };
        var picked = InvokePickRandom<string>(svc, pickList);

        Assert.Contains(picked, pickList);
        Assert.Equal(4, pickList.Count);

        return new RunSnapshot(ints, floatBits, list, picked);
    }

    private static Assembly GameCoreAssembly => Assembly.Load("Game.Core");

    private static Type GetGameCoreType(string fullName)
    {
        var t = GameCoreAssembly.GetType(fullName, throwOnError: false, ignoreCase: false);
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

    private static void AssertHasMethod(Type type, string name, Type returnType, params Type[] parameterTypes)
    {
        var mi = type.GetMethod(name, parameterTypes);
        Assert.NotNull(mi);
        Assert.Equal(returnType, mi!.ReturnType);
    }

    private static void AssertHasGenericListMethod(Type type, string methodName)
    {
        var methods = type.GetMethods(BindingFlags.Instance | BindingFlags.Public)
            .Where(m => string.Equals(m.Name, methodName, StringComparison.Ordinal))
            .Where(m => m.IsGenericMethodDefinition)
            .Where(m => m.GetGenericArguments().Length == 1)
            .Where(m => m.GetParameters().Length == 1)
            .ToArray();

        Assert.True(methods.Length >= 1, $"Expected {type.FullName}.{methodName}<T>(List<T>) to exist.");

        var hasListParam = methods.Any(m =>
        {
            var p = m.GetParameters()[0].ParameterType;
            return p.IsGenericType && p.GetGenericTypeDefinition() == typeof(List<>);
        });

        Assert.True(hasListParam, $"Expected {type.FullName}.{methodName}<T> parameter to be List<T>.");
    }

    private static T Invoke<T>(object instance, string methodName, params object?[] args)
    {
        var t = instance.GetType();
        var mi = t.GetMethod(methodName, BindingFlags.Instance | BindingFlags.Public);
        Assert.NotNull(mi);

        try
        {
            var raw = mi!.Invoke(instance, args);
            Assert.NotNull(raw);
            Assert.IsType<T>(raw);
            return (T)raw!;
        }
        catch (TargetInvocationException ex) when (ex.InnerException is not null)
        {
            ExceptionDispatchInfo.Capture(ex.InnerException).Throw();
            throw;
        }
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

    private static void InvokeShuffle<T>(object instance, List<T>? list)
    {
        var t = instance.GetType();
        var mi = FindGenericListMethod(t, "Shuffle");
        var closed = mi.MakeGenericMethod(typeof(T));

        try
        {
            closed.Invoke(instance, new object?[] { list });
        }
        catch (TargetInvocationException ex) when (ex.InnerException is not null)
        {
            ExceptionDispatchInfo.Capture(ex.InnerException).Throw();
            throw;
        }
    }

    private static T InvokePickRandom<T>(object instance, List<T>? list)
    {
        var t = instance.GetType();
        var mi = FindGenericListMethod(t, "PickRandom");
        var closed = mi.MakeGenericMethod(typeof(T));

        try
        {
            var raw = closed.Invoke(instance, new object?[] { list });
            Assert.NotNull(raw);
            Assert.IsType<T>(raw);
            return (T)raw!;
        }
        catch (TargetInvocationException ex) when (ex.InnerException is not null)
        {
            ExceptionDispatchInfo.Capture(ex.InnerException).Throw();
            throw;
        }
    }

    private static MethodInfo FindGenericListMethod(Type serviceType, string methodName)
    {
        var methods = serviceType.GetMethods(BindingFlags.Instance | BindingFlags.Public)
            .Where(m => string.Equals(m.Name, methodName, StringComparison.Ordinal))
            .Where(m => m.IsGenericMethodDefinition)
            .Where(m => m.GetGenericArguments().Length == 1)
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
