# Example Platform Architecture

Example Platform (EP) is a fictional resource scheduler used to demonstrate the wiki. It places batch jobs onto a pool of worker nodes based on requested capacity and priority.

## Overview

EP runs as a control service between job submitters and worker nodes. It accepts job requests over a REST API, queues them by priority, and assigns each job to a worker with enough free capacity.

### Key Components

- **EP Core**: Accepts job requests, maintains the queue, and makes placement decisions.
- **Node Agent**: Runs on each worker node and reports free capacity to EP Core every 10 seconds.
- **Rebalancer**: Scheduled task that moves long-running jobs off overloaded nodes.
- **Usage Reporter**: Summarizes CPU-hours per project each day for chargeback reports.

## Architecture

```
Job Submitters → EP Core (REST API) → Placement Queue
EP Core → Node Agents (heartbeats over HTTPS)
EP Core → Rebalancer → Node Agents
EP Core → Usage Reporter → Reports bucket
```

## Teams

- **Owner**: Example Platform team (Tech Lead: Jane Doe)
- **Stakeholders**: Batch users, Operations
- **Oncall**: oncall@example.com

## Status

EP is in limited beta with three pilot projects. The usage reporter is complete. Rebalancing is planned for the next quarter.

## References

- Design doc: https://wiki.example.com/pages/viewpage.action?pageId=789012
- Dashboard: https://dashboards.example.com/d/finops-cost
- Slack channel: #example-platform
