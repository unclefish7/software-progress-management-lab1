快照：0d1f50007f9bca3f52b06e1c3074fa14d5fb0720
路径：README.md

   1 | # DeepSeek Harness
   2 | 
   3 | English | [中文](README.zh.md)
   4 | 
   5 | DeepSeek Harness (`dsh`) is an open-source agent harness developed by [DeepSeek AI](https://deepseek.com).
   6 | 
   7 | It is built on an **everything-is-a-plugin** architecture and powered by [Cordis](https://github.com/cordiverse/cordis), whose design is described in [_A Programming Paradigm for Spatiotemporal Composability_](https://arxiv.org/abs/2608.25512).
   8 | 
   9 | Documentation: [https://deepseek-harness.github.io/deepseek-harness/](https://deepseek-harness.github.io/deepseek-harness/)
  10 | 
  11 | ## Developer preview
  12 | 
  13 | DeepSeek Harness is in _developer preview_ and iterating rapidly. **THERE WILL BE COMPATIBILITY-BREAKING CHANGES.**
  14 | 
  15 | Review the [safety notice](SAFETY.md) before running the project.
  16 | 
  17 | ## Run
  18 | 
  19 | ### Run from `npm`
  20 | 
  21 | Install `Node.js`, then run:
  22 | 
  23 | ```sh
  24 | npx @deepseek-ai/dsh web
  25 | ```
  26 | 
  27 | The command starts the Web UI at `http://127.0.0.1:3080` by default and opens it in the default browser for a local launch. An SSH launch only prints the host URL because the SSH client or editor owns the local forwarded address. Pass `--no-open` to run the server without opening a browser. See [Web UI guide](docs/user/guide/index.md).
  28 | 
  29 | ### Run from source
  30 | 
  31 | To run from a repository checkout:
  32 | 
  33 | ```sh
  34 | git clone https://github.com/deepseek-ai/deepseek-harness.git
  35 | cd deepseek-harness
  36 | pnpm install
  37 | pnpm run build
  38 | pnpm dsh web
  39 | ```
  40 | 
  41 | `pnpm run build` prepares the repository artifacts. `pnpm dsh web` uses those built artifacts without rebuilding.
  42 | 
  43 | ## Community and support
  44 | 
  45 | - Submit feedback or bug reports through [GitHub Discussions](https://github.com/deepseek-ai/deepseek-harness/discussions).
  46 | - Add the [`dsh-plugin`](https://github.com/topics/dsh-plugin) topic to your plugin repository for discoverability.
  47 | - Join <a href="https://discord.gg/Ycq5dCaS4">DeepSeek Harness Discord community</a>.
  48 | 
  49 | ## Contributing
  50 | 
  51 | See [CONTRIBUTING.md](CONTRIBUTING.md).
  52 | 
  53 | ## Development
  54 | 
  55 | Start with the [development guide](docs/development.md) and [architecture documentation](docs/architecture.md).
  56 | 
  57 | For agents, follow [AGENTS.md](AGENTS.md).
  58 | 
  59 | ## Citation
  60 | 
  61 | ```bibtex
  62 | @misc{deepseek-harness2026,
  63 |   title={DeepSeek Harness: Everything is a Plugin},
  64 |   author={DeepSeek-AI},
  65 |   year={2026},
  66 |   publisher={GitHub},
  67 |   howpublished={\url{https://github.com/deepseek-ai/deepseek-harness}},
  68 | }
  69 | ```
  70 | 
  71 | ## License
  72 | 
  73 | [MIT](LICENSE)
  74 | 
  75 | Third-party dependencies and their licenses are disclosed in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
