% =====================================================================
% T2-CYCLE -- Problem #17 control.
% A naive reading of m0255 ("the exception does not override any policies")
% that drops the scope guard ranks EVERY content policy above m0252, while
% m0252's own text ranks it above m0208. Two-cycle, both attackers defeated,
% and without the guard the permission silently wins.
% kernel.lp's `:- beats_tc(X,X).` must reject this.
% =====================================================================
beats(m0208, m0252).
