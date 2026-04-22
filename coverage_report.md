# Test Coverage Report

**Generated**: 2026-04-22
**Total Coverage**: 86% ✅ (Above 80% target)
**Tests**: 101 passed

## Coverage by Module

| Module | Coverage | Missing Lines |
|--------|----------|--------------|
| app/api/ai.py | 64% | 47, 56-57, 78-190, 202, 205, 239-241, 252, 293, 336, 377, 405 |
| app/api/apikeys.py | 98% | 95 |
| app/api/auth.py | 90% | 79-83 |
| app/api/categories.py | 95% | 56, 79 |
| app/api/deps.py | 74% | 31, 40, 59, 66-71, 81, 88 |
| app/api/export.py | 95% | 71-72, 82 |
| app/api/records.py | 90% | 63, 65, 67, 174, 182, 184, 188, 190, 201, 210, 240, 263, 277, 298 |
| app/api/stats.py | 97% | 132-133 |
| app/api/wallets.py | 91% | 70, 75, 79, 97, 116, 124 |
| app/core/config.py | 100% | - |
| app/core/security.py | 72% | 28-30, 56-77 |
| app/database.py | 67% | 12-16 |
| app/main.py | 91% | 41, 46 |
| app/models/* | 100% | - |
| app/schemas/* | 100% | - |
| app/services/ai_service.py | 54% | 24, 57-101, 123-124 |

## Low Coverage Areas

1. **app/api/ai.py (64%)** - Main AI recognition logic including background task
2. **app/services/ai_service.py (54%)** - AI service integration with external API
3. **app/core/security.py (72%)** - Security utilities
4. **app/database.py (67%)** - Database configuration

## HTML Report

Interactive HTML report available at:
```
coverage_html/index.html
```

To view in browser:
```bash
open coverage_html/index.html
```
