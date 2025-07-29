#!/usr/bin/env python3
"""Test script for updated cost estimation."""

from src.config.settings import CostEstimator

print('=== Updated Cost Comparison ===')
comparison = CostEstimator.get_service_comparison()

print(f'OpenAI costs:')
print(f'  Per minute: ${comparison["openai"]["cost_per_minute"]:.4f}')
print(f'  Per hour: ${comparison["openai"]["cost_per_hour"]:.2f}')

print(f'Local costs:')
print(f'  Per minute: ${comparison["local"]["cost_per_minute"]:.4f}')
print(f'  Per hour: ${comparison["local"]["cost_per_hour"]:.2f}')

print()
print('=== 10 Minute Cost Comparison ===')
cost_comp = CostEstimator.get_cost_comparison(10.0, include_summary=True)
print(f'OpenAI (with summary): ${cost_comp["openai"]["total"]:.4f}')
print(f'Local (with summary): ${cost_comp["local"]["total"]:.4f}')
print(f'Savings: ${cost_comp["savings"]["amount"]:.4f} ({cost_comp["savings"]["percentage"]:.1f}%)')
