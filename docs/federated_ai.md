# Federated AI Threat Correlation Center

The Federated AI agent architecture coordinates cross-region intelligence checkouts to detect global threat actors and adjust reputation ratings.

## Agent Node Registry

### AgentNode
- Tracks regional AI agent coordinator deployments.
- Fields: `name`, `agent_type` (SOC Agent, CTI Agent, LMS Agent, Executive Agent), `status`.

## Cross-Region Intelligence Correlation

1. **Indicator Reputation Lookup**: Queries threat reputation rankings.
2. **Connectivity Validation**: Verifies active Security Mesh federation tunnels.
3. **Consensus & Recommendations**: Active agent nodes aggregate indicators and compute containment actions.

## REST API Endpoints

- `GET /api/v1/federation` - List active agent nodes.
- `POST /api/v1/federation/register` - Register a new agent coordinator.
- `POST /api/v1/federation/correlate` - Correlate threat indicators cross-region.
- `GET /api/v1/reputation` - Lookup indicator reputation score.
- `POST /api/v1/reputation/update` - Register or update a threat reputational score.
- `POST /api/v1/reputation/feedback` - Feed ratings feedback to adjust reputation score.
