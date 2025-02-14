# Leviathan: El Soberano Digital 🐉

Bot de Discord que implementa un sistema de democracia líquida con delegación recursiva y votación por consenso.

## La Paradoja de la Libertad

En el corazón de este sistema yace una contradicción intencional:
- La UI es amigable, acogedora, diseñada para empoderar
- El núcleo es un monstruo matemático, inmutable, eterno

Esta disonancia cognitiva no es un error, sino la esencia misma del contrato social:
- Cedemos poder absoluto a un árbitro imparcial
- Ese árbitro es un monstruo, pero uno que nos protege de nosotros mismos
- La UI amigable es el velo que hace tolerable esta realidad

Como Hobbes escribió: "*El Leviatán, ese mortal dios al que debemos nuestra paz y defensa*"

## Características 🌟

- Sistema de delegación de puntos
- Votación ponderada
- Visualización de delegaciones
- Cálculo de consenso
- Sistema de propuestas y artículos
- Mecanismo de desempate con 2 puntos reservados

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

## Comandos Amigables 🌟

A pesar de su núcleo inmutable y absoluto, Leviathan se presenta con una interfaz acogedora:

### Delegación
- `!delegar @usuario <puntos>` - Delega puntos a otro usuario
- `!revocar @usuario` - Revoca delegación a un usuario
- `!poder` - Muestra tu poder de voto actual

### Votación
- `!proponer <título>` - Crea una nueva propuesta
- `!articulo <id_propuesta> <contenido>` - Añade artículo a propuesta
- `!votar <id_propuesta> <puntos>` - Vota en una propuesta

### Visualización
- `!arbol` - Muestra árbol de delegaciones
- `!consenso <id_propuesta>` - Muestra métricas de consenso

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

## Arquitectura 🏛️

El sistema se basa en tres componentes core:

1. **DelegationSystem**: Maneja la delegación de puntos
2. **VotingSystem**: Gestiona propuestas y votaciones
3. **Visualization**: Genera visualizaciones del sistema

Para más detalles técnicos, consulta [ARCHITECTURE.md](ARCHITECTURE.md)

## La Paradoja de la Seguridad

El sistema Leviathan encarna una verdad incómoda:
- La seguridad absoluta requiere restricciones absolutas
- La libertad total lleva al caos
- La paz requiere un monstruo que nos proteja de nosotros mismos

Pero este monstruo:
- Es matemáticamente justo
- No puede ser corrompido
- No tiene emociones ni prejuicios
- Está limitado por su propia naturaleza

## Cálculo de Consenso 📊

El sistema utiliza tres métricas de consenso:
- H₁₀: Consenso inmediato
- Hₑ: Consenso a largo plazo
- Hₛ: Incertidumbre

## Sistema de Desempate ⚖️

Cada votante mantiene 2 puntos reservados que pueden usarse para resolver empates entre delegados.

## Contribuir 🤝

1. Fork el repositorio
2. Crea una rama (`git checkout -b feature/amazing`)
3. Commit tus cambios (`git commit -m 'Add feature'`)
4. Push a la rama (`git push origin feature/amazing`)
5. Abre un Pull Request

## Licencia 📄

Este proyecto está bajo la Licencia GNU. Ver el archivo [LICENSE](LICENSE) para más detalles.
```
