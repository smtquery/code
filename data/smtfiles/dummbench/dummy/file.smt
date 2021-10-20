(set-logic QF_S)
 
(declare-fun x () String)

(assert (= (str.++ "ab" "ab") (str.++ "ab" x)))
(check-sat)
(get-model)