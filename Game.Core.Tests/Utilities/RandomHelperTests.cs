using Game.Core.Utilities;
using Xunit;

namespace Game.Core.Tests.Utilities;

public class RandomHelperTests
{
    [Fact]
    public void NextInt_is_within_expected_range()
    {
        for (int i = 0; i < 100; i++)
        {
            var v = RandomHelper.NextInt(2, 5);
            Assert.InRange(v, 2, 4);
        }
    }

    [Fact]
    public void NextDouble_is_within_expected_range()
    {
        for (int i = 0; i < 100; i++)
        {
            var v = RandomHelper.NextDouble();
            Assert.True(v >= 0d && v < 1d, $"Expected 0 <= v < 1 but got {v}.");
        }
    }
}
