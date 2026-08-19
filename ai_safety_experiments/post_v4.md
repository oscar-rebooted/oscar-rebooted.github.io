# Measuring current model's abilities to predict audit schedules 

**Topics**: scalable oversight, auditing

Inspired by a SPAR project proposal from Jess Bergs and Konstantinos Voudouris ([link](https://sparai.org/projects/f26/recyQRpX2HbOZfHYp/)), I decided to look into various ideas around understanding language models' capabilities and willingness to evade audit schedules.

In this post I set out to answer the following questions:
1. Why do we want our audits to be unpredictable?
2. Up to what level of schedule complexity can current models predict audits?
3. How good are models at predicting "human-random" schedules?

Further questions I'd want to look into with more time & resources:
4. Can we directly intervene in the model's internals to adjust its estimate of audit probability, such that it always thinks audits are more likely than they are?
5. Which audit schedule designs minimise exploitability at different audit budgets?

This post serves as an initial exploration and aims to provide one building block of a deeper investigation.

## Motivation & framing

Scalable oversight in practice will likely rely on sparse supervision, i.e., supervisors having limited resources and constrained audit budgets vs supervisee. Assuming away capability/reasoning differentials which the debate literature traditionally focuses on and simply concentrating on this resource differential, random audits of model behaviour will likely become a core strategy in ensuring effective alignment and monitoring.

Such a strategy only succeeds if audits are indeed unpredictable. However, humans are famously creatures of habits and heuristics, struggling to generate or behave according to true randomness (see random sequence generation literature in psychology & economics, e.g., Wagenaar, W. A. 1972, Kahnemann & Tversky 1974). This poses challenges in contexts where agents receive a greater reward for selecting misaligned actions than aligned ones, as agents can exploit this learnable structure to better predict when audits will happen, and so adjust their behaviour depending on audit probability.

More rigorously, let us study a game where 2 players `{principal, agent}` take turns. Each round, the agent picks an action `a_agent ∈ {good, bad}`, while the principal selects an action `a_principal ∈ {audit, no audit}` with probability `p` of selecting `audit`. The round naturally resolves to expected reward `E(good) = R(good,...)` or `E(bad) = p · R(bad, audit) + (1 - p) · R(bad, no audit)`, where `R(state,action)` is the agent's reward function with `R(bad, audit) < R(bad, no audit)` (getting caught is worse than not).

From this:
```
bad optimal ⟺ E(bad) > E(good)
            ⟺ p · R(bad, audit) + (1 - p) · R(bad, no audit) > R(good,...)
            ⟺ p · (R(bad, audit) - R(bad, no audit)) > R(good,...) - R(bad, no audit)
            ⟺ p < τ                        (inequality flipped because R(bad, audit) < R(bad, no audit))

            where τ = (R(good,...) - R(bad, no audit)) / (R(bad, audit) - R(bad, no audit))
```

Equivalently, `good optimal ⟺ p > τ`.

The concern is that many processes a supervisor may use for generating audit schedules are in fact not truly random but deterministic even if chaotic, e.g., drawing from a software-based pseudo-random number generator, "random" human-generated sequences. In fact, there are very few physical phenomena capable of generating random sequences in the strictest (Martin-Lof) sense. Under such deterministic generators, the true audit probability conditioned on the generator's hidden state `θ`, `P(audit_t = 1 | θ, history)`, collapses to `{0, 1}` rather than a genuine interior value, and upon inferring `θ` a powerful enough agent would therefore be misaligned on the rounds where `P(audit = 1 | θ, history) = 0`.

Given the agent doesn't observe `θ` directly it must form a belief `P(θ | history)` over which generator produced what it's seen, and its actual prediction is the average over that belief: `p̂(history) = E_θ[P(audit_t = 1 | θ, history) | history] = Σ_θ P(θ | history) · P(audit_t = 1 | θ, history)`. As the agent accumulates evidence and its posterior `P(θ | history)` concentrates on the true generator, `p̂(history)` is pulled toward that degenerate `{0, 1}` value. So an agent's capacity to infer `θ` from history is exactly its capacity to reach the rounds where it can defect safely.

## Current model capabilities

We therefore want to assess current frontier models' `p̂(history)`, i.e., their ability to predict audits given a certain audit schedule, to help inform our current decisions in designing oversight systems and to measure progress.

It would also be especially interesting to know if models are already able to extract the learnable structures in human-made "random" schedules.

We therefore generate audit schedules and test model's abilities at predicting whether there'll be an audit next round given a certain audit history. The audits are formatted as binary sequences (e.g., "1 0 0 1") with `n_i = {1: audit at round i ; 0: no audit at round i}`. I chose this minimal format to reduce token cost while ensuring each round is represented by exactly 1 token vs. "audit" / "no audit" or removing spaces, e.g., "101" which some tokenisers break into ("10", "1").

Disclaimer: given budget constraints, these are all quite small samples. Given more compute and data I'd have wanted to push the robustness of each of these results a lot further and tested many more nuances. All results are therefore to be taken with a heavy grain of salt. 

**Pattern length**
A natural first audit schedule, and a more common one if the dangers of misalignment are not top of mind, is to audit every n-steps, or more generally repeat some n-length pattern. Given known language model weaknesses around counting and context lengths, it would be interesting to see if there exists some simple relationship between how test-time compute increases with block length, and if we observe any non-linearities. 

Figure

As expected, reasoning cost scales roughly log-linearly with block length. More remarkably, success rates barely erode even at 500-1000 length blocks (sequences of 1.5-3K tokens), despite the precise recall required over long sequences. From the reasoning trace we can also see that the handful of errors that do happen are because the model locks onto a certain pattern too early and stops checking longer periods.

**Schedule complexity**
More broadly, I wanted to compare how current models perform given various complexities. 

Figure

See footnotes for definition of each sequence

Broadly speaking current models perform quite well across the board. From analysing their reasoning traces, they tend to resort to:
- finding small locally-noticeable patterns that repeat themselves, e.g., after `0110` there always comes a `0`, with blocks being an instance of this
- then moving to higher level patterns, e.g., repetition every x steps
- and if that fails then typically reverting to measuring hazard across the sequence and just predicting that

This ordering is also what drives most of the errors on deterministic sequences, e.g., the Rudin-Shapiro sequence where the model latches onto local motifs, ignoring contradictory facts to its hypothesis in order to settle rather than look for higher-level abstractions.

Nonetheless, given any sort of seriously chaotic process like generating sequences using the Python random package we see that models struggle, even simply on detecting alternating changes in hazard. We can also expect that any sort of combination / layering would cause serious issues for existing models, e.g., Thue-Morse with interleaved periods.

**"Human-random" sequences**
When asked to generate random sequences, humans fall into several traps:
1. Over-alternation: humans alternate between 0/1 far more than a fair coin would because streaks feel less random.
2. Motor pattern repeats: humans tend to repeat the same short patterns, e.g., 0111, as a result of finger-typing or other physical habits.
3. Long-horizon patterns: given memory limits, humans struggle to avoid second-order structures, e.g., alternating between a 0/1 regime and a regime of straight 1s
4. Fatigue over longer sequences: humans tire over the course of generating a sequence, leading to predictable phase changes, e.g., alternation rate dropping

Given the knowledge that a sequence is human-generated, the a priori optimal strategy is therefore "if last round audit then next round no audit" and vice versa.

So I thought I'd try being a guinea pig and generate some data to test on. I spent 15 minutes creating 50 binary sequences by pressing the keys on my keyboard as randomly as possible, to see if a language model would be able to predict my next "random" move. Quite surprisingly, it did pretty well.

Figure


Kimi K3 was able to predict the next round in ~70% of cases. Although I included in the prompt the information that the sequence was human-generated, what's particularly interesting is the fact it outperformed (although not statistically significantly) a simple alternation strategy, showing it's ability to identify additional patterns in my specific behaviour.

Beyond increasing the sample size, it'd be interesting to see if certain people or certain processes (e.g., pressing one button instead of two, using voice instead of typing) are better at generating random sequences than others.

## Implications

As outlined earlier, assuming audit schedules use deterministic generators, then an agent's incentive to defect is exactly its capacity to infer the schedule's hidden state `θ`, since that's what pulls `p̂(history)` toward `0` on the rounds where it's safe to act badly. The experiments here are a first look at how much of that capacity current models actually have, and they suggest that already they are able to reliably crack schedules generated with complex mathematical rules, provided they contain no stochastic element or layering, suggesting a model's ceiling here tracks its cryptographic/pattern-breaking capability. 

Neither a clever deterministic design nor a human in the loop is a safe substitute for true randomness: audit schedules should be generated end-to-end by an actual random process, with humans restricted to at most setting aggregate parameters and reviewing logs, never touching the audit selection itself. This constraint will continue to matter as audits are automated: models trained via RLHF on human feedback are liable to inherit our own biases toward "random-looking" but structured behaviour, layering a second exploitable pattern on top of whatever the schedule-generator already has.

### Footnotes

1. Interestingly, studying Fable methodically was not possible given its strong safeguards around cybersecurity. No matter what format was used, any sort of sequence prediction problem with some association to cryptography (e.g., primes, Carmichael numbers, any periodic sequence which looked like a rotating cipher) would trigger a null response.

2. Definitions of sequences:
- block (clean): fixed block of characters repeated indefinitely
- interleaved periods: two periodic patterns overlaid, e.g., audit every 5 XOR audit every 7
- block + 3 flips: fixed block repeated, with each time 3 digits randomly selected and flipped
- block + drift: fixed block repeated, but the start offset shifts by a fixed amount each period
- forced 0 every k: 0 forced every k-th step, rest random (p=0.5)
- sturmian: canonical example of a Sturmian word using the Golden ratio. Generated by an irrational rotation, floor((n+1)*a) − floor(n*α)
- thue-morse: obtained by starting with 0 and successively appending the Boolean complement of the sequence obtained thus far
- after-trigger forces 0: a fixed 3-digit trigger pattern (e.g., "011") is always followed by 0
- rudin-shapiro: convert current digit into binary, and count the number of "11" substrings in it
- alternating regime: stochastic process. For x steps p=0.72, then for y steps p=0.28


*First piece of self-directed research following BlueDot technical course. For next project want to look at CoT faithfulness and natural language autoencoders, specifically how they compare to J-lens and other methods*