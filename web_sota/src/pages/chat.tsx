import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Send } from "lucide-react";

export function Chat() {
    return (
        <div className="flex h-[calc(100vh-8rem)] flex-col space-y-4">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold tracking-tight text-white">Chat</h2>
                    <p className="text-slate-400">
                        Intended for a future embedded assistant. MCP tools (
                        <code className="text-slate-500">generate_song</code>, <code className="text-slate-500">get_status</code>, …) are
                        invoked from your <strong className="text-slate-300">MCP client</strong> (IDE, Claude Desktop, …), not from this
                        static page.
                    </p>
                </div>
            </div>

            <Card className="flex flex-1 flex-col overflow-hidden border-slate-800 bg-slate-950/50">
                <CardContent className="flex flex-1 flex-col items-center justify-center p-8 text-center">
                    <p className="max-w-lg text-sm text-slate-500">
                        No chat session is active. This UI does not call the model. Connect an MCP-capable host to{" "}
                        <code className="text-slate-600">songgeneration-mcp</code> per the repo README.
                    </p>
                </CardContent>
                <div className="border-t border-slate-800 bg-slate-900/30 p-4">
                    <div className="flex gap-2">
                        <input
                            disabled
                            className="flex-1 cursor-not-allowed rounded-md border border-slate-800 bg-slate-950 px-4 py-2 text-sm text-slate-500"
                            placeholder="Disabled — use an MCP client for tool calls"
                        />
                        <Button size="icon" disabled className="bg-slate-700">
                            <Send className="h-4 w-4" />
                        </Button>
                    </div>
                </div>
            </Card>
        </div>
    );
}
