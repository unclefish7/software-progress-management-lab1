快照：0d1f50007f9bca3f52b06e1c3074fa14d5fb0720
路径：packages/core/system-prompt/README.md

   1 | ---
   2 | description: "System-prompt assembly for users and maintainers adding prompt sections, variables, tool-schema sources, or configuring the model-facing prompt."
   3 | kind: "package-reference"
   4 | ---
   5 | 
   6 | # @deepseek-ai/dsh-system-prompt
   7 | 
   8 | English | [中文](README.zh.md)
   9 | 
  10 | ## Summary
  11 | 
  12 | `dsh-system-prompt` lets agents receive one ordered system prompt and the available tool schemas for each model step. Use it to add prompt sections, dynamic runtime facts, reusable variables, or tool schemas, or to control the fixed harness identity, deployment persona, runtime context, and model-facing tool order. Agent-scoped contributions override same-named global defaults without affecting other agents. Invalid complete-prompt combinations and unresolved variables fail assembly instead of sending a malformed prompt.
  13 | 
  14 | ## Table of Contents
  15 | 
  16 | - [Use this package](#use-this-package)
  17 | - [Understand the implementation](#understand-the-implementation)
  18 | - [Further Exploration](#further-exploration)
  19 | - [Model Experience](#model-experience)
  20 | - [Known Limitations and Deferred Work](#known-limitations-and-deferred-work)
  21 | - [Dev Note](#dev-note)
  22 | 
  23 | -----
  24 | 
  25 | <a id="use-this-package"></a>
  26 | ## Use this package
  27 | 
  28 | Mount `dsh-system-prompt` wherever agents run: it provides `ctx.systemPrompt`, the registry every prompt contribution lands in. Contributions are scoped — registering through `agent.ctx` affects that agent alone and shadows a same-named global.
  29 | 
  30 | <a id="configure-the-prompt"></a>
  31 | ### Configure the prompt
  32 | 
  33 | The config owns the fixed opener, runtime context, deployment persona prefix and suffix, and tool order; everything else comes from registered contributions.
  34 | 
  35 | ```yaml
  36 | - name: '@deepseek-ai/dsh-system-prompt'
  37 |   config:
  38 |     includeHarnessIdentity: true
  39 |     includeRuntimeContext: true
  40 |     personaPrefix: 'You are the deployment assistant.'
  41 |     toolOrder: ['<unlisted-tools>']
  42 | ```
  43 | 
  44 | | Field | Default | Meaning |
  45 | |---|---|---|
  46 | | `includeHarnessIdentity` | `true` | Include the fixed `You are an AI agent powered by DeepSeek Harness.` first-party opener at order −1000. Set false only when a compatibility deployment owns the complete system prompt. |
  47 | | `includeRuntimeContext` | `true` | Include ordered dynamic runtime context in assembly |
  48 | | `personaPrefix` | `''` | Global persona prefix template at order `0`, before first-party guidance |
  49 | | `personaSuffix` | `''` | Global `deployment:persona-suffix` template at order `10200`, after first-party guidance |
  50 | | `toolOrder` | — | Explicit model-facing tool order with one `'<unlisted-tools>'` rest entry |
  51 | 
  52 | The generated [configuration catalog](../../../docs/config-catalog.md#deepseek-aidsh-system-prompt) is the exhaustive source for every accepted field. A `toolOrder` list without exactly one rest entry or with duplicates fails at load; a listed name with no registered tool rejects every `assemble()`.
  53 | 
  54 | ### Contribute a prompt section
  55 | 
  56 | Sections carry static or context-resolved text with an `order`; they are concatenated in ascending order and equal orders use code-unit name order. Repository-owned contributors resolve centrally allocated positions through `ctx.systemPrompt.getSectionOrder(name)`; runtime-context contributors use `getContextOrder(name)`. External contributions may use any finite order. A `complete: true` section becomes the exact complete prompt after assembly; more than one effective complete section makes assembly fail.
  57 | 
  58 | ```text
  59 | ctx.systemPrompt.section({
  60 |   name: 'tool:bash',
  61 |   order: 100,
  62 |   text: 'Prefer bash for file and process operations.',
  63 | })
  64 | ```
  65 | 
  66 | Set `interpolate: false` on a section to preserve its text literally, including `{{…}}` groups in generated tool documentation. Other sections interpolate variables by default.
  67 | 
  68 | ### Contribute a prompt variable
  69 | 
  70 | Variables are referenced from section text as `{{name}}` and resolved at each assembly; scoped variables shadow a same-named global for that agent. The loop supplies `model` and `cwd`; any plugin can register the facts it owns.
  71 | 
  72 | ```text
  73 | ctx.systemPrompt.variable('cwd', ({ agent }) => agent?.session.header.cwd)
  74 | ```
  75 | 
  76 | ### Contribute tool schemas
  77 | 
  78 | Tool-schema providers are evaluated per assembly and contribute the model-visible `ToolSchema` set; `ToolRuntime` registers itself automatically, so most tools need no manual wiring here. A provider returns the post-restriction visible set plus the pre-restriction name universe used by `toolOrder`.
  79 | 
  80 | ### Suppress runtime context
  81 | 
  82 | `suppressRuntimeContext()` removes every dynamic runtime-context contribution for the calling scope without disabling the services that own the underlying facts; multiple suppressors compose and the effect restores context when none remains.
  83 | 
  84 | -----
  85 | 
  86 | <a id="understand-the-implementation"></a>
  87 | ## Understand the implementation
  88 | 
  89 | <details>
  90 | <summary>Implementation internals — click to expand</summary>
  91 | 
  92 | This section explains how the package realizes the behavior above; the observable contract is covered in [Use this package](#use-this-package).
  93 | 
  94 | ### Design concept
  95 | 
  96 | The package is a registry plus a cooperative assembly pipeline. One `assemble()` call merges the global layer with the requested scope's layer, detaches tool parameters, canonicalizes section order by number and then name, runs the scope-filtered `system-prompt/assemble` waterfall, restores an effective complete section as the sole prompt section, and applies any active runtime-context suppressor. Sections and dynamic contexts are separate inputs: sections become prompt text, while contexts become sourced user-role snapshots in model history under the loop. Tool schemas are part of the assembly by design — "what the model is told it can do" is one coherent thing, even though adapters transmit schemas as a separate wire field.
  97 | 
  98 | ### Source map
  99 | 
 100 | | File | Role |
 101 | |---|---|
 102 | | [`src/index.ts`](src/index.ts) | Plugin entry: `SystemPrompt` service, config, assembly pipeline, `renderPrompt` |
 103 | | [`src/invariant.ts`](src/invariant.ts) | Invariant companion |
 104 | 
 105 | ### Assembly and rendering
 106 | 
 107 | Assembly resolves and renders in two stages: `assemble()` returns sections with resolved-but-uninterpolated text, the ordered tool schemas, and every registered variable resolved against the context, while `renderPrompt()` interpolates `{{variable}}` references unless a section sets `interpolate: false`, drops empty sections, and joins with blank lines — strictly, an unknown reference, a registered-but-valueless reference, or a malformed complete group throws, because a malformed prompt is worse than a loud failure. `toolOrder` canonicalizes the collected tools before the waterfall (registration order is a plugin-load artifact); a waterfall listener that mutates the list owns the determinism of what it emits.
 108 | 
 109 | ### Scoping
 110 | 
 111 | Scoped sections, variables, and tool providers shadow globals for one agent, and the assembly waterfall dispatches scope-filtered. Registry-change notifications (`system-prompt/change`) are deliberately unfiltered because a global change affects every scope.
 112 | 
 113 | </details>
 114 | 
 115 | -----
 116 | 
 117 | <a id="further-exploration"></a>
 118 | ## Further Exploration
 119 | 
 120 | The package-level contract is enough for most consumers; read these when you need the surrounding domain.
 121 | 
 122 | - [System-prompt subsystem](../../../docs/subsystems/system-prompt.md) — the exact cross-package types and generated service API.
 123 | - [tools package](../tools/README.md) — the tool registry whose schemas flow into assembly.
 124 | - [Prompt variables Agent Note](../../../.agents/notes/implemented/architecture/2026-07-05-prompt-variables-and-tool-guidance-ownership.md) — who owns which prompt facts.
 125 | - [First-party prompt order Agent Note](../../../.agents/notes/archived/architecture/2026-08-25-sparse-first-party-prompt-section-orders.md) — the sparse named order allocation.
 126 | - [Core group map](../README.md) — how the core packages compose.
 127 | 
 128 | -----
 129 | 
 130 | <a id="model-experience"></a>
 131 | ## Model Experience
 132 | 
 133 | ### System prompt
 134 | 
 135 | #### What the model sees
 136 | 
 137 | First-party sections render the harness identity, deployment persona prefix (including the model-name introduction), reusable instructions (including the generated tools SDK and structured-output guidance), then the environment-bearing suffix: harness source (`10000`), Web surface (`10100`), and deployment persona suffix (`10200`). External section orders and assembly listeners remain authoritative. `includeHarnessIdentity: false` omits only that fixed opener. Empty sections disappear; scoped sections and variables can shadow globals for one agent. The `system-prompt/assemble` waterfall determines the delivered prompt and tool schemas unless one effective section declares itself complete — that exact section then becomes the whole system prompt while the waterfall's contexts, tools, and variables remain. The rendered prompt reaches the model as a system-role message of derived history — surface node 0, or the latest system node after an in-history update — neither the loop request nor `request/header` carries a separate `system` field. If the complete rendering is empty, the loop clears every active system node through logged empty replacements, so no older prompt remains in model history. Ordered dynamic contexts are separate from sections and become sourced user-role snapshots only when present; `includeRuntimeContext: false` or a scoped suppressor removes them all.
 138 | 
 139 | ##### Harness identity
 140 | 
 141 | ```markdown
 142 | You are an AI agent powered by DeepSeek Harness.
 143 | ```
 144 | 
 145 | #### Token effect
 146 | 
 147 | Identity is a fixed per-request cost when enabled. Persona prefixes, suffixes, and plugin text are repeated per request and scale with their rendered content.
 148 | 
 149 | #### KV Cache effect
 150 | 
 151 | Prefix-stable while identity, persona, variables, section text, and order render identically: an unchanged rendering leaves the system nodes untouched unless an incapable route or a new request series must consolidate retained in-history prompts. Without `systemPromptUpdate`, non-empty prompt text is consolidated at the first system node through logged per-node replacements, so a head rewrite loses prefix reuse from its first changed token; when the prepared call declares `systemPromptUpdate: 'in-history'`, the agent loop appends a non-empty changed prompt after the cached history inside a continuing request series, so the prefix through that history stays reusable ([decision rule](../agent-loop/README.md#understand-the-implementation)). With the same model, persona prefix, tools, and preceding instructions, different source paths, local Web URLs, or persona suffix values leave the reusable first-party prefix unchanged. Persona prefix changes can alter the early prefix. Any change may invalidate reuse from the first changed token; provider cache sharing and measured hit rates are not guaranteed.
 152 | 
 153 | ### Tool schemas
 154 | 
 155 | #### What the model sees
 156 | 
 157 | For shipped tools, the model receives the per-agent-visible subset of the [generated tool schemas](../../../docs/tool-catalog.md#deepseek-aidsh-tools), ordered by configuration or lexicographically after restrictions and assembly interception. Extensions can contribute additional definitions through the same registry. Sections and schema providers are separate assembly inputs. A restriction does not remove a section registration: tool-guidance plugins use `text({ scope })` and `ctx.tools.get(name, scope)` to return empty text or select applicable fragments. Arbitrary static sections are not automatically rewritten.
 158 | 
 159 | #### Token effect
 160 | 
 161 | Schema tokens repeat on every request. Restricting a tool removes its entire schema cost for that agent but not a separate prompt section; reordering changes cache shape but not semantic content.
 162 | 
 163 | #### KV Cache effect
 164 | 
 165 | Prefix-stable while the visible schema set, rendering, and order are unchanged. Registration, restriction, or reordering may invalidate reuse from the first changed schema token.
 166 | 
 167 | ## Known Limitations and Deferred Work
 168 | 
 169 | <a id="known-limitations-and-deferred-work"></a>
 170 | 
 171 | 
 172 | These limits define when prompt assembly needs special care. They are current package constraints, not a task backlog.
 173 | 
 174 | - **Deployment-authored prompt text is config/composition only** — this plugin owns the global persona prefix and suffix defaults, creator plugins may register agent-scoped shadows, and other sections come from the plugin that owns the fact; there is no end-user prompt-editing API.
 175 | - **No inline escape syntax in interpolated text** — use `interpolate: false` when a whole section must preserve literal braces.
 176 | - **`toolOrder` misconfiguration surfaces at prompt assembly (the first turn), not at boot** — only shape violations throw at config load.
 177 | 
 178 | 
 179 | <a id="dev-note"></a>
 180 | ### Dev Note
 181 | 
 182 | <details>
 183 | <summary>Working context for maintainers — click to expand</summary>
 184 | 
 185 | None.
 186 | 
 187 | </details>
