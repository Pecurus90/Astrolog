"""The only writer of the database: one thread runs the stages in order, stops cooperatively and
publishes its state. It runs generators and knows nothing of what a stage does."""
