# Runtime target and evidence

- Licensed Mount & Blade: Warband data format: official stable 1.174.
- Current target: [WSE2 v1.1.5.4](https://github.com/Ruslan-700/WSE2-Releases/releases/tag/v1.1.5.4), released 2026-10-14.
- Historical input: ZOMBIEEE (Invasion) Beta 0.4 compiled Warband module.
- WSE2 Lua documentation: https://github.com/Ruslan-700/WSE2-Releases/blob/master/Warband/WSE2%20SDK/luaGuide.html

WSE2 is a third-party modified runtime, **not** a successor official Warband game release and not Bannerlord. The target version is pinned for reproducibility and may be updated after regression testing.

The old mod's Python `module_*.py` source was not included. Prefer reversible overlays, Lua instrumentation and selective reconstruction. Mod compatibility with WSE2, scene loading, actual bot spawning and wave completion remain **unverified** until recorded in Windows gameplay evidence. Do not infer performance benefits solely from the engine's changelog.
