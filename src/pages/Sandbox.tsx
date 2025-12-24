import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { ThemeToggle } from "@/components/ThemeToggle";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Loader2, ExternalLink, Search, Sparkles } from "lucide-react";
import { Link } from "react-router-dom";

interface SnapshotResponse {
  snapshot: string;
  url: string;
  cached: boolean;
  token_count?: number;
}

interface PromptMatch {
  line: number;
  content: string;
  context: string;
}

interface PromptResponse {
  matches: PromptMatch[];
  prompt: string;
  total_matches: number;
}

// API base URL - use environment variable or default to localhost:8000
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const Sandbox = () => {
  const [url, setUrl] = useState("");
  const [currentUrl, setCurrentUrl] = useState("");
  const [prompt, setPrompt] = useState("");
  const [highlightedLines, setHighlightedLines] = useState<Set<number>>(new Set());

  // Fetch snapshot
  const {
    data: snapshotData,
    isLoading: isLoadingSnapshot,
    error: snapshotError,
    refetch: refetchSnapshot,
  } = useQuery<SnapshotResponse>({
    queryKey: ["playwright-snapshot", currentUrl],
    queryFn: async () => {
      if (!currentUrl) throw new Error("URL is required");
      
      let response;
      try {
        response = await fetch(`${API_BASE_URL}/api/playwright/snapshot`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            url: currentUrl,
            use_cache: true,
          }),
        });
      } catch (fetchError: any) {
        // Network error - server might be down or CORS issue
        throw new Error(
          `Cannot connect to backend at ${API_BASE_URL}. ` +
          `Make sure the backend server is running. Error: ${fetchError.message}`
        );
      }

      if (!response.ok) {
        let errorMessage = "Failed to fetch snapshot";
        try {
          const error = await response.json();
          errorMessage = error.detail || error.message || error.error || errorMessage;
        } catch (e) {
          errorMessage = `HTTP ${response.status}: ${response.statusText}`;
        }
        throw new Error(errorMessage);
      }

      return response.json();
    },
    enabled: !!currentUrl,
    retry: 1,
  });

  // Test prompt mutation
  const testPromptMutation = useMutation<PromptResponse, Error, string>({
    mutationFn: async (promptText: string) => {
      if (!snapshotData?.snapshot) {
        throw new Error("No snapshot available");
      }

      const response = await fetch(`${API_BASE_URL}/api/playwright/test-prompt`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          snapshot: snapshotData.snapshot,
          prompt: promptText,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to test prompt");
      }

      return response.json();
    },
    onSuccess: (data) => {
      // Highlight matching lines
      const linesToHighlight = new Set(data.matches.map((m) => m.line));
      setHighlightedLines(linesToHighlight);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (url.trim()) {
      setCurrentUrl(url.trim());
      setHighlightedLines(new Set());
    }
  };

  const handleTestPrompt = () => {
    if (prompt.trim() && snapshotData) {
      testPromptMutation.mutate(prompt.trim());
    }
  };

  const normalizeUrlForIframe = (url: string): string => {
    if (!url) return "";
    let normalized = url.trim();
    if (!normalized.startsWith("http://") && !normalized.startsWith("https://")) {
      normalized = "https://" + normalized;
    }
    return normalized;
  };

  const renderSnapshotWithHighlights = (snapshot: string) => {
    const lines = snapshot.split("\n");
    return lines.map((line, index) => {
      const lineNumber = index + 1;
      const isHighlighted = highlightedLines.has(lineNumber);
      return (
        <div
          key={index}
          className={`font-mono text-xs p-1 ${
            isHighlighted
              ? "bg-yellow-200 dark:bg-yellow-900/30 border-l-2 border-yellow-500"
              : ""
          }`}
        >
          <span className="text-muted-foreground mr-2 select-none">{lineNumber}</span>
          {line}
        </div>
      );
    });
  };

  return (
    <div className="min-h-screen bg-background">
      <header className="container mx-auto px-4 py-6 flex justify-between items-center">
        <Link to="/" className="text-lg font-semibold hover:underline">
          ← Back to Home
        </Link>
        <ThemeToggle />
      </header>

      <main className="container mx-auto px-4 py-8 max-w-7xl">
        <div className="text-center space-y-4 mb-8">
          <h1 className="text-4xl md:text-5xl font-bold text-foreground">
            Playwright Sandbox
          </h1>
          <p className="text-xl text-muted-foreground">
            Test drive the Playwright MCP server - See how AI "views" websites
          </p>
        </div>

        {/* URL Input */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Enter a URL to Preview</CardTitle>
            <CardDescription>
              Enter any website URL to see its structured accessibility snapshot
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="flex gap-2">
              <Input
                type="text"
                placeholder="e.g., google.com, github.com, amazon.com"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                className="flex-1"
              />
              <Button type="submit" disabled={!url.trim() || isLoadingSnapshot}>
                {isLoadingSnapshot ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Loading...
                  </>
                ) : (
                  <>
                    <Search className="mr-2 h-4 w-4" />
                    Generate Snapshot
                  </>
                )}
              </Button>
            </form>
            {snapshotData?.cached && (
              <p className="text-sm text-muted-foreground mt-2">
                ✓ Using cached snapshot for faster results
              </p>
            )}
          </CardContent>
        </Card>

        {/* Error Display */}
        {snapshotError && (
          <Card className="mb-6 border-destructive">
            <CardContent className="pt-6 space-y-2">
              <p className="text-destructive font-semibold">
                Error: {snapshotError instanceof Error ? snapshotError.message : "Failed to load snapshot"}
              </p>
              {(snapshotError instanceof Error && 
                (snapshotError.message.toLowerCase().includes("blocking") || 
                 snapshotError.message.toLowerCase().includes("x.com") ||
                 snapshotError.message.toLowerCase().includes("twitter"))) && (
                <div className="mt-3 p-3 bg-muted rounded-lg">
                  <p className="text-sm text-muted-foreground">
                    <strong>Note:</strong> Some websites (like x.com/twitter) have strict anti-bot measures 
                    that prevent automated access. Try a different URL like:
                  </p>
                  <ul className="list-disc list-inside mt-2 text-sm text-muted-foreground space-y-1">
                    <li>wikipedia.org</li>
                    <li>github.com</li>
                    <li>google.com</li>
                    <li>example.com</li>
                  </ul>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Dual View Panel */}
        {currentUrl && (
          <div className="grid md:grid-cols-2 gap-6 mb-6">
            {/* Left: Live Website */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <ExternalLink className="h-5 w-5" />
                  Live Website
                </CardTitle>
                <CardDescription>
                  The website as you see it
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="border rounded-lg overflow-hidden bg-muted">
                  <iframe
                    src={normalizeUrlForIframe(currentUrl)}
                    className="w-full h-[600px] border-0"
                    title="Live website preview"
                    sandbox="allow-same-origin allow-scripts allow-forms allow-popups"
                  />
                </div>
              </CardContent>
            </Card>

            {/* Right: AI View */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Sparkles className="h-5 w-5" />
                  AI View (Accessibility Snapshot)
                </CardTitle>
                <CardDescription>
                  {snapshotData?.token_count && (
                    <span>~{snapshotData.token_count.toLocaleString()} tokens</span>
                  )}
                </CardDescription>
              </CardHeader>
              <CardContent>
                {isLoadingSnapshot ? (
                  <div className="flex items-center justify-center h-[600px]">
                    <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                  </div>
                ) : snapshotData ? (
                  <ScrollArea className="h-[600px] border rounded-lg p-4 bg-muted">
                    <pre className="text-xs">
                      {renderSnapshotWithHighlights(snapshotData.snapshot)}
                    </pre>
                  </ScrollArea>
                ) : (
                  <div className="flex items-center justify-center h-[600px] text-muted-foreground">
                    No snapshot available
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        )}

        {/* Try a Prompt Section */}
        {snapshotData && (
          <Card>
            <CardHeader>
              <CardTitle>Try a Prompt</CardTitle>
              <CardDescription>
                Ask the AI to find elements in the snapshot (e.g., "Find the login button")
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <Label htmlFor="prompt">Prompt</Label>
                  <div className="flex gap-2 mt-2">
                    <Textarea
                      id="prompt"
                      placeholder='e.g., "Find the login button" or "Where is the search field?"'
                      value={prompt}
                      onChange={(e) => setPrompt(e.target.value)}
                      className="flex-1"
                      rows={2}
                    />
                    <Button
                      onClick={handleTestPrompt}
                      disabled={!prompt.trim() || testPromptMutation.isPending}
                    >
                      {testPromptMutation.isPending ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        "Test"
                      )}
                    </Button>
                  </div>
                </div>

                {testPromptMutation.data && (
                  <div className="space-y-2">
                    <p className="text-sm font-medium">
                      Found {testPromptMutation.data.total_matches} match
                      {testPromptMutation.data.total_matches !== 1 ? "es" : ""}
                    </p>
                    <ScrollArea className="h-48 border rounded-lg p-4">
                      {testPromptMutation.data.matches.map((match, idx) => (
                        <div
                          key={idx}
                          className="mb-4 p-2 bg-muted rounded text-xs"
                        >
                          <p className="font-semibold">Line {match.line}:</p>
                          <p className="text-muted-foreground">{match.content}</p>
                        </div>
                      ))}
                    </ScrollArea>
                  </div>
                )}

                {testPromptMutation.error && (
                  <p className="text-sm text-destructive">
                    Error: {testPromptMutation.error.message}
                  </p>
                )}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Info Section */}
        {!currentUrl && (
          <Card>
            <CardHeader>
              <CardTitle>How It Works</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <h3 className="font-semibold mb-2">1. Enter a URL</h3>
                <p className="text-sm text-muted-foreground">
                  Type any website URL (e.g., google.com) and click "Generate Snapshot"
                </p>
              </div>
              <div>
                <h3 className="font-semibold mb-2">2. View the Comparison</h3>
                <p className="text-sm text-muted-foreground">
                  See the live website on the left and the structured accessibility snapshot on the right
                </p>
              </div>
              <div>
                <h3 className="font-semibold mb-2">3. Test with Prompts</h3>
                <p className="text-sm text-muted-foreground">
                  Use the "Try a Prompt" section to see how an AI agent would find elements in the snapshot
                </p>
              </div>
              <div className="pt-4 border-t">
                <p className="text-sm text-muted-foreground">
                  <strong>Token Savings:</strong> The structured snapshot is much more efficient than sending
                  screenshots or full HTML to AI models, reducing costs and improving accuracy.
                </p>
              </div>
            </CardContent>
          </Card>
        )}
      </main>
    </div>
  );
};

export default Sandbox;

