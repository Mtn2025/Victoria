import { Component, ErrorInfo, ReactNode } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";

interface Props {
    children?: ReactNode;
    fallback?: ReactNode;
}

interface State {
    hasError: boolean;
    error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
    public state: State = {
        hasError: false
    };

    public static getDerivedStateFromError(error: Error): State {
        return { hasError: true, error };
    }

    public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
        console.error("Uncaught error:", error, errorInfo);
    }

    public render() {
        if (this.state.hasError) {
            if (this.props.fallback) return this.props.fallback;

            return (
                <div className="flex items-center justify-center min-h-[200px] p-6">
                    <Card className="max-w-md w-full border-red-500/30 bg-red-950/10">
                        <CardHeader>
                            <CardTitle className="text-red-400 flex items-center gap-2">
                                Algo salió mal
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <p className="text-sm text-slate-300">
                                {this.state.error?.message || "Ocurrió un error inesperado."}
                            </p>
                            <Button
                                variant="outline"
                                onClick={() => this.setState({ hasError: false })}
                                className="w-full border-red-500/30 text-red-400 hover:bg-red-950/30"
                            >
                                Reintentar
                            </Button>
                        </CardContent>
                    </Card>
                </div>
            );
        }

        return this.props.children;
    }
}
