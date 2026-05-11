-- The statement I used to create my model
--l2_reg is a way of preventing overfitting, I added a bunch of related/correlated calculated fields
--and putting l2_reg at 2.5 was intended to help address that correlation.


CREATE OR REPLACE MODEL `flight_delay_ML.dep_delay_logistic`
OPTIONS (
  model_type = 'LOGISTIC_REG',
  input_label_cols = ['dep_del15'],
  data_split_method = 'RANDOM',
  data_split_eval_fraction = 0.2,
  l2_reg = 2.5
) AS

SELECT *
FROM `flight_delay_ML.flight_data_with_calculated_fields`;