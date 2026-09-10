# Per-repo fleet start config for songgeneration-mcp
# Edit ports/backend target here - start.ps1 is fleet-standard.
@{
    Name         = 'songgeneration-mcp'
    BackendPort  = 10885
    FrontendPort = 10884
    HealthPath   = '/api/health'
    WebRoot      = 'D:\Dev\repos\songgeneration-mcp\web_sota'
    Backend = @{
        Kind          = 'uvicorn'
        UvicornTarget = 'songgeneration_mcp.server:app'
        SyncExtras    = @('dev')
        Env           = @{ WEB_PORT = '10885' }
    }
    Frontend = @{
        Kind           = 'vite-npm'
        PackageManager = 'npm'
        PortEnvVar     = 'VITE_PORT'
        ApiTargetEnv   = 'VITE_API_TARGET'
    }
}
