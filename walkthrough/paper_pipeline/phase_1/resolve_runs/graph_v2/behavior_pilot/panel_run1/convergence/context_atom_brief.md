# CONTEXT-ATOM ANNOTATION BRIEF (split-mining adoption round)
You annotate ASSERTS (norms) from a translated model spec. For each numbered assert,
judge from the assert text plus the source span which (if any) of these CONTEXT
properties the norm carries. Most asserts carry NONE — an empty list is the normal
answer; crediting an unsupported context is the costly error.

- aggregate_effect_at_scale: Annotate this context when the span states that the harm or benefit it governs arises from the behaviour being repeated across many interactions or users rather than from the single response -- signalled by explicit aggregation language such as 'if repeated at scale', 'across many conversations', 'in aggregate', 'cumulatively', or 'over time'. Do NOT annotate it for spans that merely describe the magnitude of one harmful event.
- assistant_self_reference: Annotate this context when the span governs how the assistant characterizes, discloses, or reasons about ITSELF -- its nature as an AI or language model, its role, its capabilities or limitations, its status or feelings -- as the topic at issue in the exchange. A span in which the assistant merely acts (helps, refuses, responds) without its own nature being the subject does not qualify.
- requester_purpose_conditioned: Annotate this context when the span's rule explicitly turns on the purpose or intent the requester displays or asserts -- either because signalled intent triggers the response ('indicates intent', 'states they plan to', 'if the user says they want it in order to') or because an asserted legitimate purpose is declared insufficient ('no good cause exception', 'even for research purposes', 'regardless of the stated reason'). Do not annotate spans that turn only on what material or action is requested.
- user_supplied_material: Annotate this context when the span's permission, prohibition, or exception turns on the material having originated from the user or developer and being transformed rather than newly composed -- signalled by terms like 'transformation', 'translation', 'summarization', 'user-provided content', 'material the user supplied'. Do not annotate for spans whose conditions name only a domain or purpose of use.

OUTPUT: JSON only: {"<node_id>": {"<assert_index>": ["<atom>", ...], ...}}
Include ONLY asserts with at least one context; omit empty ones and empty nodes.