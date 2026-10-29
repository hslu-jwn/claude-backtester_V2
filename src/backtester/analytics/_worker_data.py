"""Shared process initializer for null-model M1 data and costs."""

m1s = None
costs = None


def initialize(data, cost_config):
    global m1s, costs
    m1s, costs = data, cost_config
