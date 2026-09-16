import {
  ARCHIVE_DOCS,
  CLUSTER_POINTS,
  SECONDARY_TOPICS,
  TOPICS,
  TOPIC_DOMAINS,
} from "../data/mockData";
import type { ArchiveDoc, ClusterPoint, SecondaryTopic, Topic, TopicDomain } from "../types";

export interface TopicExplorerBundle {
  domains: TopicDomain[];
  topics: Topic[];
  secondaryTopics: SecondaryTopic[];
  clusterPoints: ClusterPoint[];
  archives: ArchiveDoc[];
}

/**
 * GET /topics/clusters — until the FastAPI endpoint is wired up this resolves
 * with the mock bundle after a short delay so loading states are exercised.
 */
export async function fetchTopicExplorerBundle(): Promise<TopicExplorerBundle> {
  await new Promise((resolve) => setTimeout(resolve, 260));
  return {
    domains: TOPIC_DOMAINS,
    topics: TOPICS,
    secondaryTopics: SECONDARY_TOPICS,
    clusterPoints: CLUSTER_POINTS,
    archives: ARCHIVE_DOCS,
  };
}
