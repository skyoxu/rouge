using System;
using System.Collections.Generic;

namespace Game.Core.Services;

public interface IRngService
{
    void SetSeed(int seed);

    int NextInt(int min, int max);

    float NextFloat();

    void Shuffle<T>(List<T> list);

    T PickRandom<T>(List<T> list);
}

public sealed class RngService : IRngService
{
    private Random _rng = new();

    public void SetSeed(int seed)
    {
        _rng = new Random(seed);
    }

    public int NextInt(int min, int max)
    {
        if (min >= max)
        {
            throw new ArgumentOutOfRangeException(nameof(min), "min must be less than max.");
        }

        return _rng.Next(min, max);
    }

    public float NextFloat()
    {
        return (float)_rng.NextDouble();
    }

    public void Shuffle<T>(List<T> list)
    {
        ArgumentNullException.ThrowIfNull(list);

        for (int i = list.Count - 1; i > 0; i--)
        {
            int j = NextInt(0, i + 1);
            (list[i], list[j]) = (list[j], list[i]);
        }
    }

    public T PickRandom<T>(List<T> list)
    {
        ArgumentNullException.ThrowIfNull(list);
        if (list.Count == 0)
        {
            throw new ArgumentException("list must not be empty.", nameof(list));
        }

        int index = NextInt(0, list.Count);
        return list[index];
    }
}

