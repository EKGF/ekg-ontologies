# Lifecycles and states

[Documentation index](../README.md#documentation)

The [lifecycle ontology](../ekgf-lifecycle.ttl) defines lifecycles,
phases, states and their assignments. The
[lifecycle registry](../dataset/well-known-lifecycles.ttl) contains
reusable lifecycles; [class bindings](../dataset/lifecycle-bindings.ttl)
supply the default assignments.

## Available lifecycles

A lifecycle is a named sequence of states, optionally grouped into
phases. Each lifecycle has a namespace of its own,
`https://ekgf.org/lifecycle/<slug>#`, because lifecycles share state
names such as Draft and Deprecated.

- `continuous-improvement`: plan, build, run and evolve, in nine
  states from identified to decommissioned
- `achievement`: draft, active, achieved, deprecated
- `software-delivery`: development, test, user acceptance test,
  production
- `publication`: from working draft to published, and on to
  superseded or withdrawn
- `execution`: admitted, queued, running, then done, failed or
  cancelled

## Selecting a lifecycle

Which lifecycle a thing follows is decided in this order.

1. The lifecycle the thing names itself, with
   `ekg-lifecycle:followsLifecycle`.
2. The lifecycle that applies to a class of the thing, with
   `ekg-lifecycle:appliesTo`.

The [class bindings](../dataset/lifecycle-bindings.ttl) are defaults.
They are policy, so an organization that wants its stories, say, to
follow a lifecycle of its own replaces the binding in its own data.

## Recording a state

```turtle
@prefix ex: <https://example.org/> .
@prefix ekg-lifecycle: <https://ekgf.org/ontology/lifecycle#> .
@prefix continuous-improvement: <https://ekgf.org/lifecycle/continuous-improvement#> .

ex:my-story
    ekg-lifecycle:followsLifecycle
        <https://ekgf.org/lifecycle/continuous-improvement> ;
    ekg-lifecycle:hasState continuous-improvement:Deployed .
```

The state IRI identifies a state within that lifecycle. A resource
following a different lifecycle must use the states defined for it.
For the distinction between a release's lifecycle state and its
approval records, see [publication approvals](publication.md#approvals).
