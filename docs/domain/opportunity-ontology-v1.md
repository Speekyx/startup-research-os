# Opportunity Ontology V1

## 1. Purpose

The Opportunity Ontology defines the domain vocabulary used by the Startup Research OS.

The system does not define a good opportunity solely as a painful problem. An opportunity can exist because users want to solve a problem, accomplish a goal, have fun, create something, learn, compete, socialize, explore, express themselves, or experience something novel.

## 2. Core entity

An `Opportunity` is a structured, evidence-backed hypothesis that a digital product could create meaningful value for a defined audience in a defined market under a plausible product and distribution model.

An opportunity is not automatically:

- a validated business,
- a guaranteed successful startup,
- a proven product-market fit,
- or a prediction of future revenue.

## 3. Opportunity dimensions

### 3.1 Market type

Examples:

- B2B
- B2C
- B2B2C
- Prosumer
- Creator
- Developer
- Student
- Professional
- Hobbyist
- Community
- Enterprise

Multiple labels may apply.

### 3.2 Product type

Examples:

- SaaS
- Web App
- AI Application
- Marketplace
- Social Platform
- Community
- Tool
- Game
- Educational Product
- Content Platform
- Generator
- Tracker
- Assistant
- Automation
- Browser Extension
- API

Multiple labels may apply.

### 3.3 User motivation

First-class motivation categories include:

- PROBLEM
- UTILITY
- ENTERTAINMENT
- CREATIVITY
- CURIOSITY
- LEARNING
- COMPETITION
- SOCIAL
- EXPRESSION
- STATUS
- DISCOVERY
- EMOTION
- ACHIEVEMENT
- COLLECTION
- PERSONALIZATION
- EXPERIENCE
- MONEY

A motivation can be primary or secondary.

### 3.4 User behavior

Examples:

- CREATE
- DISCOVER
- CONSUME
- PLAY
- LEARN
- COMPARE
- PREDICT
- COLLECT
- SHARE
- COMPETE
- CUSTOMIZE
- TRACK
- DISCUSS
- BUY
- SELL
- COLLABORATE
- AUTOMATE

### 3.5 Value proposition

Examples:

- TIME_SAVING
- MONEY_SAVING
- MONEY_MAKING
- CONVENIENCE
- KNOWLEDGE
- ENTERTAINMENT
- CREATIVITY
- SOCIAL_CONNECTION
- STATUS
- PERSONAL_GROWTH
- DISCOVERY
- EXPERIENCE

### 3.6 Demand signals

#### Pain signals

- complaint
- frustration
- repeated problem
- workaround
- manual process
- expensive solution
- missing feature

#### Desire signals

- explicit request
- wish statement
- product request
- curiosity
- expressed intent
- positive reaction
- desire to try

#### Behavioral signals

- engagement
- repeated usage
- shares
- comments
- searches
- communities
- purchases
- subscriptions
- downloads where reliable

#### Market signals

- new competitors
- product launches
- funding
- search growth
- category growth
- technology changes
- regulatory changes
- platform changes

### 3.7 Retention mechanisms

Examples:

- HABIT
- NEW_CONTENT
- PROGRESSION
- COLLECTION
- COMPETITION
- SOCIAL_GRAPH
- PERSONALIZATION
- EVENTS
- UTILITY
- WORKFLOW
- COMMUNITY
- CURIOSITY

### 3.8 Monetization models

Examples:

- SUBSCRIPTION
- FREEMIUM
- CREDITS
- ONE_TIME_PURCHASE
- ADVERTISING
- AFFILIATE
- MARKETPLACE_FEE
- TRANSACTION_FEE
- SPONSORSHIP
- API_USAGE
- B2B_LICENSE
- DONATION

### 3.9 Distribution channels

Examples:

- SEO
- SOCIAL
- VIRAL
- COMMUNITY
- CONTENT
- APP_STORE
- PRODUCT_HUNT
- WORD_OF_MOUTH
- PAID_ADS
- PARTNERSHIP
- MARKETPLACE
- EXTENSION_STORE
- DIRECT_SALES

### 3.10 Risks

Examples:

- TECHNICAL_RISK
- DATA_DEPENDENCY
- PLATFORM_DEPENDENCY
- LEGAL_RISK
- COMPETITION_RISK
- ACQUISITION_RISK
- MONETIZATION_RISK
- RETENTION_RISK

## 4. Geographic market

Market analysis may be global, regional, country-level, or segment-level.

Relevant dimensions include:

- market size
- interest
- growth
- purchasing power
- competition
- local alternatives
- language
- payment methods
- distribution channels
- cultural factors
- regulatory factors

A global score must not erase meaningful country-level differences.

## 5. Behavioral loop

A product should be modeled as a possible user loop when appropriate:

`trigger → action → value → reward → reason to return`

Examples:

### Creative product

`discover → create → result → share → create again`

### Competitive product

`predict → result → compare → compete → predict again`

### Productivity product

`problem → workflow → saved effort → habit → workflow`

The presence and quality of a loop are signals, not guarantees of retention.

## 6. Opportunity representation

Conceptually:

```text
Opportunity
├── Market
├── Product Type
├── Target Users
├── Motivations
├── Behaviors
├── Value Proposition
├── Demand Signals
├── Retention Mechanisms
├── Monetization
├── Distribution
├── Competition
├── Market Intelligence
├── Risks
├── Evidence
└── Scores
```

## 7. Important distinction

The system must distinguish:

- Observed: directly supported by collected data.
- Inferred: derived from observations.
- Predicted: model-generated estimate.
- Recommended: decision proposed by the system.

These categories must not be conflated in user-facing output.

## 8. Ontology evolution

V1 is the baseline. Material semantic changes require V2 or an explicit extension/ADR.

Do not silently add a new fundamental category if doing so changes scoring, storage, or interpretation contracts.
