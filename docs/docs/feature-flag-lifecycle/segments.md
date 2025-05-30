---
title: Segments Reference
description: Complete reference for Flagsmith segments, including operators, limits, and data types.
---

# Segments Reference

## Core Concepts

### Segment
A subset of identities defined by rules that match identity traits. Each segment:
- Belongs to a single environment
- Contains one or more rules
- Can override feature states
- Can be project-wide or feature-specific

### Segment Rule
A condition that determines segment membership based on identity traits:
- Evaluated in order (top to bottom)
- Can use multiple operators
- Supports various data types
- Can be combined with AND/OR logic

## Data Types

### Trait Types
| Type | Description | Example Value |
|------|-------------|---------------|
| String | Text values | `"user@example.com"` |
| Boolean | True/false values | `true` |
| Integer | Whole numbers | `42` |
| Float | Decimal numbers | `3.14` |

### Type Coercion Rules
| From Type | To Type | Coercion Rules |
|-----------|---------|----------------|
| String → Boolean | `"true"`, `"True"`, `"1"` → `true` |
| String → Integer | Parsed as base-10 |
| String → Float | Parsed as decimal |

## Operators

### Comparison Operators
| Operator | Description | Example | Data Types |
|----------|-------------|---------|------------|
| `=` | Exact match | `age = 21` | All |
| `!=` | Not equal | `country != US` | All |
| `>` | Greater than | `logins > 10` | Number |
| `>=` | Greater than/equal | `spent >= 100` | Number |
| `<` | Less than | `age < 18` | Number |
| `<=` | Less than/equal | `version <= 2.1` | Number |

### String Operators
| Operator | Description | Example |
|----------|-------------|---------|
| `Contains` | Substring match | `email Contains @company.com` |
| `Does not contain` | No substring match | `plan Does not contain free` |
| `Matches regex` | Regex pattern match | `email Matches .*@gmail\.com` |
| `In` | List membership | `country In US,UK,CA` |

### Special Operators
| Operator | Description | Example |
|----------|-------------|---------|
| `% Split` | Percentage bucket | `% Split = 25` |
| `Is set` | Trait exists | `premium_until Is set` |
| `Is not set` | Trait doesn't exist | `trial_ended Is not set` |
| `SemVer` | Version comparison | `version SemVer >= 2.1.0` |
| `Modulo` | Division remainder | `user_id % 2|0` |

## SDK Version Requirements

| SDK | Modulo | In |
|-----|--------|-----|
| Python | 2.3.0 | 3.3.0 |
| Java | 5.1.0 | 7.1.0 |
| .NET | 4.2.0 | 5.0.0 |
| Node.js | 2.4.0 | 2.5.0 |
| Ruby | 3.1.0 | 3.2.0 |
| PHP | 3.1.0 | 4.1.0 |
| Go | 2.2.0 | 3.1.0 |
| Rust | 0.2.0 | 1.3.0 |
| Elixir | 1.1.0 | 2.0.0 |

## System Limits

| Resource | Limit |
|----------|-------|
| Segments per project | 100 |
| Segment overrides per environment | 100 |
| Rules per segment override | 100 |
| Segment rule value size | 1000 bytes |

## Evaluation Precedence

1. Identity Override
2. Segment Override (first matching)
3. Environment Default

## Performance Characteristics

### Local Evaluation
- Sub-millisecond evaluation time
- No network requests
- Rules evaluated in-memory
- Linear scaling with rule count

### Remote Evaluation
- Network latency dependent
- Cached segment results
- Server-side evaluation
- Constant time regardless of rule count
