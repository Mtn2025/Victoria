# Deuda Técnica - Fase B (Frontend)

| ID | Tipo | Descripción | Ubicación | Severidad |
|----|------|-------------|-----------|-----------|
| DT-FRONT-001 | Arquitectura | **Ausencia de Routing Real**. Se usa Redux para cambiar "Tabs" en lugar de URL Routing. | `App.tsx`, `Sidebar.tsx` | ⚠️ Media |
| DT-FRONT-002 | Funcionalidad | **Botón Guardar Inactivo**. El botón en `ConfigPage` no ejecuta ninguna acción. | `ConfigPage.tsx` | 🔴 Crítica |
| DT-FRONT-003 | Estándar | **Configuración Monolítica**. El tipo `BrowserConfig` es un objeto plano gigante, difícil de mantener. | `types/config.ts` | ℹ️ Baja |
| DT-FRONT-004 | Seguridad | **API Key en LocalStorage**. Se lee directamente del storage sin una capa de abstracción de seguridad robusta. | `api.ts` | ⚠️ Media |

---
**Acciones Inmediatas Requeridas:**
1. Resolver **DT-FRONT-002** para permitir guardar la configuración del agente.
