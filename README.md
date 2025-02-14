# Tamagotchi Demócrata 🗳️

Sistema de democracia líquida con delegación fraccionada y votación por consenso, implementado como bot de Discord.

## 🚀 Inicio Rápido

1. Configura el token:
```bash
echo "DISCORD_TOKEN=tu_token_aquí" > .env
```

2. Instala dependencias:
```bash
pip install -r requirements.txt
```

3. Ejecuta:
```bash
python bot.py
```

## 📚 Guía de Comandos

### Sistema de Delegación
| Comando | Descripción | Uso |
|---------|-------------|-----|
| `!delegar` | Delega puntos de voto | `!delegar @usuario 500 [True/False]` |
| `!revocar` | Revoca una delegación | `!revocar @usuario` |
| `!perfil` | Muestra tu información | `!perfil` |
| `!arbol` | Visualiza delegaciones | `!arbol` |

### Sistema de Propuestas
| Comando | Descripción | Uso |
|---------|-------------|-----|
| `!proponer` | Crea propuesta nueva | `!proponer` |
| `!articulo` | Añade artículo | `!articulo ID_PROPUESTA` |
| `!votar` | Vota en propuesta | `!votar ID_PROPUESTA PUNTOS` |

## ⚙️ Características Clave

- **Delegación Fraccionada**: 1000 puntos = 1 voto completo
- **Visualización Orgánica**: 
  - 🌳 Árboles para delegadores
  - 🥔 Tubérculos para votantes directos
  - 🍎 Frutos indican estados
- **Métricas de Consenso**:
  - Inmediato (log10)
  - Largo plazo (ln)
  - Incertidumbre (Shannon)

## 📋 Estructura

```
Tamagotchi democrata/
├── bot.py              # Bot principal
├── commands.py         # Comandos Discord
├── delegation.py       # Sistema delegación
├── voting.py          # Sistema votación
├── utility.py         # Utilidades
├── visualization.py   # Visualizaciones
└── Data/
    ├──/Logs
    ├── delegations.json
    ├── constitution.json
    └── propositions.json
```

Para más detalles técnicos, consulta [ARCHITECTURE.md](ARCHITECTURE.md)
