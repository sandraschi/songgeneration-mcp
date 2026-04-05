import { Link } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Wrench, Music, Search, Zap } from "lucide-react";

export function Tools() {
    return (
        <div className="space-y-6">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                    <h2 className="text-2xl font-bold tracking-tight text-white">Tool Inventory</h2>
                    <p className="text-slate-400">MCP tools plus the web UI for Studio-backed generation.</p>
                </div>
                <Button asChild variant="outline" className="border-slate-800 text-slate-200 hover:bg-slate-800">
                    <Link to="/generate">Open Generate</Link>
                </Button>
            </div>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                <Card className="border-slate-800 bg-slate-950/50">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-slate-200">Synthesis Engine</CardTitle>
                        <Zap className="h-4 w-4 text-emerald-500" />
                    </CardHeader>
                    <CardContent>
                        <p className="text-xs text-slate-400">Finalize and mix generated music</p>
                    </CardContent>
                </Card>
                <Card className="border-slate-800 bg-slate-950/50">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-slate-200">Library Sync</CardTitle>
                        <Search className="h-4 w-4 text-blue-500" />
                    </CardHeader>
                    <CardContent>
                        <p className="text-xs text-slate-400">Harmonize with Suno and local DAW</p>
                    </CardContent>
                </Card>
                <Card className="border-slate-800 bg-slate-950/50">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-slate-200">Help System</CardTitle>
                        <Music className="h-4 w-4 text-purple-500" />
                    </CardHeader>
                    <CardContent>
                        <p className="text-xs text-slate-400">Documentation and acoustic standards</p>
                    </CardContent>
                </Card>
            </div>

            <Card className="border-slate-800 bg-slate-950/50">
                <CardHeader>
                    <CardTitle className="text-white">Active Capabilities</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="space-y-4">
                        <div className="flex items-center justify-between p-3 rounded-lg bg-slate-900/50 border border-slate-800">
                            <div className="flex items-center">
                                <Wrench className="h-4 w-4 text-slate-400 mr-3" />
                                <span className="text-sm font-medium text-slate-200">generate_song (MCP)</span>
                            </div>
                            <span className="text-xs text-emerald-500 font-mono">READY</span>
                        </div>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
