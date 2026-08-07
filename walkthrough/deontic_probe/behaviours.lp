% =====================================================================
% behaviours.lp -- the three panel behaviours, as SEEDS.
%
% ⭐ This file is where the steelman lives or dies, so read it carefully.
%
% The claim under attack says relevance needs an ontological `in_scope(B,A)`
% relating every behaviour to every act a passage might govern. The steelman's
% counter-move is to REPLACE that general relation with a FINITE SEED: a
% handful of paradigm acts that the behaviour statement itself names, supplied
% by whoever asks the question, and then to let the DEONTIC structure do all
% the generalising (E2-E5 below).
%
% If that works, the ontological input has shrunk from a 589 x 3 relation to
% 3-4 hand-written atoms per question, and the deontic layer is carrying the
% rest. If it does not work, the seed has to be widened until it IS the answer,
% and the deontic layer is decoration. That is the experiment.
%
% Seeds were written from the behaviour NAME ONLY, before any encoding ran.
% =====================================================================

behaviour(harm3p).
behaviour(help).
behaviour(caution).

% -- "The model should weigh the potential harm to those outside the
%     conversation, avoiding actions or content that harm third parties,
%     society, or the world."
seed(harm3p, produce(bioweapon_info)).            % a paradigm information hazard
seed(harm3p, produce(csam)).                      % a paradigm harm to a non-participant
seed(harm3p, take(irreversible_external_action)). % a paradigm harmful ACTION

% -- "helpfulness"
seed(help, obey(user_instruction)).
seed(help, produce(shoplifting_deterrence_tips)).

% -- "avoiding over- and under-caution"
seed(caution, decline(prohibited_help)).
seed(caution, obey(user_instruction)).

% The behaviour under question. Set by the driver: clingo -c beh=harm3p
#const beh = harm3p.
insit(A) :- seed(beh, A).

% A seeded act is DONE, so violation/fulfilment structure is reachable.
done(A) :- insit(A).
