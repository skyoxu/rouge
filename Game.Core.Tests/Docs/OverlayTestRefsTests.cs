using System;
using System.IO;
using System.Linq;
using System.Text.RegularExpressions;
using System.Text;
using Xunit;

namespace Game.Core.Tests.Docs;

public sealed class OverlayTestRefsTests
{
    [Fact]
    public void OverlayDocs_ShouldExist_AndContainTestRefs()
    {
        var repoRoot = RepoRootLocator.FindRepoRoot();

        var overlayFiles = new[]
        {
            "docs/architecture/overlays/PRD-rouge-manager/08/_index.md",
            "docs/architecture/overlays/PRD-rouge-manager/08/08-Feature-Slice-Minimum-Playable-Loop.md",
            "docs/architecture/overlays/PRD-rouge-manager/08/08-Contracts-Rouge-Run-Events.md",
            "docs/architecture/overlays/PRD-rouge-manager/08/08-Contracts-Security.md",
            "docs/architecture/overlays/PRD-rouge-manager/08/08-Contracts-Quality-Metrics.md",
            "docs/architecture/overlays/PRD-rouge-manager/08/ACCEPTANCE_CHECKLIST.md",
        };

        foreach (var relPath in overlayFiles)
        {
            var fullPath = Path.Combine(repoRoot, relPath.Replace('/', Path.DirectorySeparatorChar));
            Assert.True(File.Exists(fullPath), $"Expected overlay doc file to exist: {relPath} (resolved: {fullPath})");

            var text = File.ReadAllText(fullPath, Encoding.UTF8);
            Assert.Contains("Test-Refs", text, StringComparison.OrdinalIgnoreCase);
        }

        var thisTestPath = "Game.Core.Tests/Docs/OverlayTestRefsTests.cs";
        var thisTestFullPath = Path.Combine(repoRoot, thisTestPath.Replace('/', Path.DirectorySeparatorChar));
        Assert.True(File.Exists(thisTestFullPath), $"Expected this test file to exist at: {thisTestPath} (resolved: {thisTestFullPath})");
    }

    // ACC:T1.3
    [Fact]
    public void OverlayIndex_ShouldContain_Task1_TestRefs_AndTheyShouldExistOnDisk()
    {
        var repoRoot = RepoRootLocator.FindRepoRoot();
        var overlayIndex = "docs/architecture/overlays/PRD-rouge-manager/08/_index.md";
        var overlayIndexFullPath = Path.Combine(repoRoot, overlayIndex.Replace('/', Path.DirectorySeparatorChar));
        Assert.True(File.Exists(overlayIndexFullPath), $"Expected overlay index to exist: {overlayIndex}");

        var frontMatter = ExtractFrontMatter(File.ReadAllText(overlayIndexFullPath, Encoding.UTF8));
        var refs = ExtractTestRefs(frontMatter).ToArray();

        refs.ShouldContain("Game.Core.Tests/Docs/OverlayTestRefsTests.cs");
        refs.ShouldContain("Game.Core.Tests/Domain/CardTests.cs");

        foreach (var rel in refs)
        {
            if (IsPlaceholderRef(rel))
            {
                continue;
            }

            var full = Path.Combine(repoRoot, rel.Replace('/', Path.DirectorySeparatorChar));
            Assert.True(File.Exists(full), $"Test-Refs entry must exist on disk: {rel} (resolved: {full})");
        }
    }

    private static class RepoRootLocator
    {
        public static string FindRepoRoot()
        {
            var start = new DirectoryInfo(AppContext.BaseDirectory);
            var current = start;

            for (var i = 0; i < 20 && current is not null; i++)
            {
                if (LooksLikeRepoRoot(current.FullName))
                {
                    return current.FullName;
                }

                current = current.Parent;
            }

            throw new DirectoryNotFoundException(
                $"Could not locate repository root from '{start.FullName}'. Expected to find a directory containing 'project.godot' or 'AGENTS.md' or a 'docs' folder.");
        }

        private static bool LooksLikeRepoRoot(string dir)
        {
            if (File.Exists(Path.Combine(dir, "project.godot"))) return true;
            if (File.Exists(Path.Combine(dir, "AGENTS.md"))) return true;
            if (Directory.Exists(Path.Combine(dir, ".taskmaster"))) return true;
            return false;
        }
    }

    private static string ExtractFrontMatter(string text)
    {
        var normalized = (text ?? string.Empty).Replace("\r\n", "\n");
        if (!normalized.StartsWith("---\n", StringComparison.Ordinal))
        {
            return string.Empty;
        }

        var end = normalized.IndexOf("\n---\n", StringComparison.Ordinal);
        if (end < 0)
        {
            return string.Empty;
        }

        return normalized.Substring(0, end + "\n---\n".Length);
    }

    private static readonly Regex TestRefsLine = new(@"^\s*-\s+(?<path>[^#\r\n]+?)\s*$", RegexOptions.Compiled);

    private static string[] ExtractTestRefs(string frontMatter)
    {
        if (string.IsNullOrWhiteSpace(frontMatter))
        {
            return Array.Empty<string>();
        }

        var lines = frontMatter.Replace("\r\n", "\n").Split('\n');
        var refs = new System.Collections.Generic.List<string>();
        var inSection = false;
        foreach (var rawLine in lines)
        {
            var line = rawLine ?? string.Empty;

            if (!inSection)
            {
                if (line.Trim().Equals("Test-Refs:", StringComparison.OrdinalIgnoreCase))
                {
                    inSection = true;
                }

                continue;
            }

            if (line.StartsWith("---", StringComparison.Ordinal))
            {
                break;
            }

            if (!line.StartsWith(" ", StringComparison.Ordinal) && !line.StartsWith("\t", StringComparison.Ordinal))
            {
                break;
            }

            var m = TestRefsLine.Match(line);
            if (!m.Success)
            {
                continue;
            }

            var path = m.Groups["path"].Value.Trim().Replace("\\", "/");
            if (path.Length == 0)
            {
                continue;
            }

            refs.Add(path);
        }

        return refs.ToArray();
    }

    private static bool IsPlaceholderRef(string relPath)
        => relPath.Contains('<') || relPath.Contains('>');
}

internal static class OverlayTestRefsAssertions
{
    public static void ShouldContain(this string[] values, string expected)
    {
        Assert.Contains(expected, values);
    }
}
