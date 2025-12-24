import { ThemeToggle } from "@/components/ThemeToggle";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Brain, Server, Shield, Sparkles, ExternalLink } from "lucide-react";
import { Link } from "react-router-dom";

const Index = () => {
  return (
    <div className="min-h-screen bg-background">
      <header className="container mx-auto px-4 py-6 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2">
          <img 
            src="/ChatGPT Image Nov 24, 2025, 02_59_09 PM.png" 
            alt="MCP Messenger Logo" 
            className="h-8 w-8 object-contain"
          />
          <span className="font-semibold text-lg">MCP Messenger</span>
        </Link>
        <ThemeToggle />
      </header>
      
      <main className="container mx-auto px-4 py-12 max-w-5xl">
        <div className="text-center space-y-6 mb-16">
          {/* Logo Section */}
          <div className="flex items-center justify-center gap-8 mb-8">
            <img 
              src="/stk8sqYZ_400x400.png" 
              alt="Playwright Logo" 
              className="h-16 md:h-20 w-auto object-contain opacity-90 hover:opacity-100 transition-opacity"
            />
            <div className="text-2xl text-muted-foreground">×</div>
            <img 
              src="/ChatGPT Image Nov 24, 2025, 02_59_09 PM.png" 
              alt="MCP Messenger Logo" 
              className="h-16 md:h-20 w-auto object-contain opacity-90 hover:opacity-100 transition-opacity"
            />
          </div>
          
          <h1 className="text-5xl md:text-7xl font-bold text-foreground">
            Playwright Sandbox
          </h1>
          <p className="text-xl text-muted-foreground">
            MCP Server Preview
          </p>
          <div className="pt-6">
            <Link to="/sandbox">
              <Button size="lg" className="gap-2">
                <Sparkles className="h-5 w-5" />
                Try Playwright Sandbox
                <ExternalLink className="h-4 w-4" />
              </Button>
            </Link>
          </div>
        </div>

        {/* Playwright Sandbox CTA */}
        <section className="mb-16">
          <Card className="border-primary/50 bg-primary/5">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="h-6 w-6 text-primary" />
                Playwright Sandbox Preview
              </CardTitle>
              <CardDescription>
                Test drive the Playwright MCP server directly on this website. See how AI "views" websites through structured accessibility snapshots.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Link to="/sandbox">
                <Button variant="outline" className="w-full md:w-auto gap-2">
                  <ExternalLink className="h-4 w-4" />
                  Open Sandbox
                </Button>
              </Link>
            </CardContent>
          </Card>
        </section>

        {/* Key Features */}
        <section className="mb-16">
          <h2 className="text-2xl font-semibold mb-8 text-center">Key Features</h2>
          <div className="grid md:grid-cols-3 gap-6">
            <Card>
              <CardHeader>
                <Brain className="w-8 h-8 text-primary mb-2" />
                <CardTitle>LangGraph Integration</CardTitle>
                <CardDescription>
                  Built on LangChain/LangGraph for stateful, production-grade agent workflows
                </CardDescription>
              </CardHeader>
            </Card>

            <Card>
              <CardHeader>
                <Server className="w-8 h-8 text-primary mb-2" />
                <CardTitle>FastAPI Backend</CardTitle>
                <CardDescription>
                  High-performance Python web framework with automatic OpenAPI documentation
                </CardDescription>
              </CardHeader>
            </Card>

            <Card>
              <CardHeader>
                <Shield className="w-8 h-8 text-primary mb-2" />
                <CardTitle>Secure & Scalable</CardTitle>
                <CardDescription>
                  Stateless architecture supporting horizontal scaling and API key authentication
                </CardDescription>
              </CardHeader>
            </Card>
          </div>
        </section>

        {/* System Architecture */}
        <section className="mb-16">
          <Card>
            <CardHeader>
              <CardTitle className="text-xl">System Architecture</CardTitle>
              <CardDescription>
                Simple, single-process web application with dual MCP endpoints
              </CardDescription>
            </CardHeader>
            <CardContent className="grid md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <h3 className="font-semibold">/mcp/manifest</h3>
                <p className="text-sm text-muted-foreground">
                  Returns static JSON declaring the LangChain agent as an MCP tool
                </p>
                <div className="bg-muted p-3 rounded font-mono text-xs">
                  GET /mcp/manifest
                </div>
              </div>

              <div className="space-y-2">
                <h3 className="font-semibold">/mcp/invoke</h3>
                <p className="text-sm text-muted-foreground">
                  Executes agent with user query and returns structured response
                </p>
                <div className="bg-muted p-3 rounded font-mono text-xs">
                  POST /mcp/invoke
                </div>
              </div>
            </CardContent>
          </Card>
        </section>

        {/* Success Metrics */}
        <section className="mb-16">
          <h2 className="text-2xl font-semibold mb-8 text-center">Success Metrics</h2>
          <div className="grid sm:grid-cols-2 md:grid-cols-4 gap-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">P95 Latency</CardTitle>
                <CardDescription>Under 5 seconds</CardDescription>
              </CardHeader>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Uptime Target</CardTitle>
                <CardDescription>99.9% availability</CardDescription>
              </CardHeader>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Error Rate</CardTitle>
                <CardDescription>Less than 0.1%</CardDescription>
              </CardHeader>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">MCP Compliance</CardTitle>
                <CardDescription>100% protocol adherence</CardDescription>
              </CardHeader>
            </Card>
          </div>
        </section>

        {/* Technology Stack */}
        <section className="mb-16">
          <h2 className="text-2xl font-semibold mb-8 text-center">Technology Stack</h2>
          <div className="grid sm:grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { name: "Python 3.11+", desc: "Core Runtime" },
              { name: "FastAPI", desc: "Web Framework" },
              { name: "LangGraph", desc: "Agent Framework" },
              { name: "Docker", desc: "Containerization" }
            ].map((tech) => (
              <Card key={tech.name}>
                <CardHeader>
                  <CardTitle className="text-base">{tech.name}</CardTitle>
                  <CardDescription className="text-sm">{tech.desc}</CardDescription>
                </CardHeader>
              </Card>
            ))}
          </div>
        </section>
      </main>
    </div>
  );
};

export default Index;
