from neo4j import GraphDatabase
from typing import Optional
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)


class Neo4jService:
    """Neo4j 数据库操作服务"""

    def __init__(self, uri: str, username: str, password: str, database: str = "neo4j"):
        self.uri = uri
        self.username = username
        self.password = password
        self.database = database
        self._driver: Optional[GraphDatabase.driver] = None

    def connect(self) -> None:
        """建立Neo4j连接"""
        self._driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))
        logger.info(f"Connected to Neo4j at {self.uri}")

    def close(self) -> None:
        """关闭Neo4j连接"""
        if self._driver:
            self._driver.close()
            logger.info("Neo4j connection closed")

    @contextmanager
    def session(self):
        """获取数据库会话的上下文管理器"""
        if not self._driver:
            self.connect()
        session = self._driver.session(database=self.database)
        try:
            yield session
        finally:
            session.close()

    def add_nodes(self, label: str, nodes: list[dict]) -> int:
        """批量插入节点"""
        query = f"""
        UNWIND $nodes AS node
        MERGE (n:{label} {{id: node.id}})
        SET n += node.properties
        RETURN count(n) as created_count
        """
        with self.session() as session:
            result = session.run(query, nodes=nodes)
            record = result.single()
            return record["created_count"] if record else 0

    def add_edges(self, label: str, edges: list[dict]) -> int:
        """批量插入边（关系）"""
        query = f"""
        UNWIND $edges AS edge
        MATCH (source {{id: edge.source_id}})
        MATCH (target {{id: edge.target_id}})
        MERGE (source)-[r:{label} {{id: edge.id}}]->(target)
        SET r += edge.properties
        RETURN count(r) as created_count
        """
        with self.session() as session:
            result = session.run(query, edges=edges)
            record = result.single()
            return record["created_count"] if record else 0

    def delete_nodes(self, node_ids: list[str], cascade: bool = True) -> int:
        """批量删除节点"""
        if cascade:
            query = """
            MATCH (n {id: $node_id})
            DETACH DELETE n
            """
        else:
            query = """
            MATCH (n {id: $node_id})
            DELETE n
            """

        deleted_count = 0
        with self.session() as session:
            for node_id in node_ids:
                result = session.run(query, node_id=node_id)
                summary = result.consume()
                deleted_count += summary.counters.nodes_deleted

        return deleted_count

    def delete_edges(self, edge_ids: list[str]) -> int:
        """批量删除边"""
        query = """
        MATCH ()-[r {id: $edge_id}]-()
        DELETE r
        """

        deleted_count = 0
        with self.session() as session:
            for edge_id in edge_ids:
                result = session.run(query, edge_id=edge_id)
                summary = result.consume()
                deleted_count += summary.counters.relationships_deleted

        return deleted_count

    def execute_operation(self, operation: str, data: dict) -> dict:
        """执行数据库操作"""
        handlers = {
            "add_nodes": self._handle_add_nodes,
            "add_edges": self._handle_add_edges,
            "delete_nodes": self._handle_delete_nodes,
            "delete_edges": self._handle_delete_edges,
        }

        handler = handlers.get(operation)
        if not handler:
            raise ValueError(f"Unknown operation: {operation}")

        return handler(data)

    def _handle_add_nodes(self, data: dict) -> dict:
        label = data.get("label")
        nodes = data.get("nodes", [])
        count = self.add_nodes(label, nodes)
        return {"operation": "add_nodes", "count": count, "status": "success"}

    def _handle_add_edges(self, data: dict) -> dict:
        label = data.get("label")
        edges = data.get("edges", [])
        count = self.add_edges(label, edges)
        return {"operation": "add_edges", "count": count, "status": "success"}

    def _handle_delete_nodes(self, data: dict) -> dict:
        node_ids = data.get("node_ids", [])
        cascade = data.get("cascade", True)
        count = self.delete_nodes(node_ids, cascade)
        return {"operation": "delete_nodes", "count": count, "status": "success"}

    def _handle_delete_edges(self, data: dict) -> dict:
        edge_ids = data.get("edge_ids", [])
        count = self.delete_edges(edge_ids)
        return {"operation": "delete_edges", "count": count, "status": "success"}