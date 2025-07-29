#!/usr/bin/env python3
"""Test script for cost estimation functions."""

from src.config.settings import CostEstimator

print('=== Summary Cost Estimation ===')
for minutes in [1, 5, 10, 30, 60]:
    cost = CostEstimator.estimate_summary_cost(minutes)
    print(f'{minutes} min: ${cost["total"]:.4f} total (${cost["per_minute"]:.4f}/min, ${cost["per_hour"]:.2f}/hour)')

print()
print('=== Full Cost Comparison (with summary) ===')
comparison = CostEstimator.get_cost_comparison(10.0, include_summary=True)
print(f'OpenAI (10 min): ${comparison["openai"]["total"]:.4f}')
print(f'Local (10 min): ${comparison["local"]["total"]:.4f}')
print(f'Savings: ${comparison["savings"]["amount"]:.4f} ({comparison["savings"]["percentage"]:.1f}%)')

print()
print('=== Transcription vs Summary breakdown ===')
openai_cost = CostEstimator.estimate_openai_cost(10.0, include_summary=True)
print(f'Transcription: ${openai_cost["transcription"]:.4f}')
print(f'Summary: ${openai_cost["summary"]:.4f}')
print(f'Total: ${openai_cost["total"]:.4f}')

print()
print('=== Cost Comparison Without Summary ===')
comparison_no_summary = CostEstimator.get_cost_comparison(10.0, include_summary=False)
print(f'OpenAI (10 min, no summary): ${comparison_no_summary["openai"]["total"]:.4f}')
print(f'Local (10 min, no summary): ${comparison_no_summary["local"]["total"]:.4f}')
print(f'Savings without summary: ${comparison_no_summary["savings"]["amount"]:.4f} ({comparison_no_summary["savings"]["percentage"]:.1f}%)')
