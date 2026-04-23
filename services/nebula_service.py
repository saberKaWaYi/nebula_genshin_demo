from __future__ import annotations

import logging
logger = logging.getLogger(__name__)

from typing import Optional
from pydantic import ValidationError
from models.schemas import AddEdgesData, AddNodesData, DeleteEdgesData, DeleteNodesData

import re
_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

import json

from nebula3.Config import Config
from nebula3.gclient.net import ConnectionPool

class NebulaService:
    """NebulaGraph 数据库操作服务"""

    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        min_connection_pool_size: int = 1,
        max_connection_pool_size: int = 1,
    ):
        if min_connection_pool_size > max_connection_pool_size:
            logger.error(
                "min_connection_pool_size must be <= max_connection_pool_size "
                f"({min_connection_pool_size} > {max_connection_pool_size})"
            )
            raise ValueError(
                "min_connection_pool_size must be <= max_connection_pool_size "
                f"({min_connection_pool_size} > {max_connection_pool_size})"
            )
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.min_connection_pool_size = min_connection_pool_size
        self.max_connection_pool_size = max_connection_pool_size
        self._pool: Optional[ConnectionPool] = None
        self._session = None

    def connect(self) -> None:
        """建立 Nebula 连接。"""
        config = Config()
        config.min_connection_pool_size = self.min_connection_pool_size
        config.max_connection_pool_size = self.max_connection_pool_size

        self._pool = ConnectionPool()
        if not self._pool.init([(self.host, self.port)], config):
            logger.error(f"Failed to connect to Nebula at {self.host}:{self.port}")
            raise ConnectionError(f"Failed to connect to Nebula at {self.host}:{self.port}")

        self._session = self._pool.get_session(self.username, self.password)
        if not self._session:
            logger.error(f"Failed to get session from Nebula at {self.username}:{self.password}")
            raise ConnectionError(f"Failed to get session from Nebula at {self.host}:{self.port}")
        logger.info(
            "Connected to Nebula at %s:%s with username %s and password %s",
            self.host,
            self.port,
            self.username,
            self.password,
        )

    def create_space(
        self,
        space_name: str,
        partition_num: int = 5,
        replica_factor: int = 1,
        vid_type: str = "FIXED_STRING(128)",
    ) -> None:
        """CREATE SPACE IF NOT EXISTS。"""
        name = self._validate_identifier(space_name)
        opts = [f"partition_num={partition_num}", f"replica_factor={replica_factor}"]
        if vid_type:
            opts.append(f"vid_type={vid_type}")
        self._execute(f"CREATE SPACE IF NOT EXISTS `{name}`({', '.join(opts)});")
        logger.info("Ensured Nebula space exists: %s", name)

    def drop_space(self, space_name: str) -> None:
        """DROP SPACE IF EXISTS。"""
        name = self._validate_identifier(space_name)
        self._execute(f"DROP SPACE IF EXISTS `{name}`;")
        logger.info("Dropped Nebula space if existed: %s", name)

    def select_space(self, space_name: str) -> None:
        """USE 指定图空间。"""
        validated = self._validate_identifier(space_name)
        self._execute(f"USE `{validated}`;")

    def create_tag(self, space_name: str, tag_name: str, properties: dict[str, str]) -> None:
        """CREATE TAG IF NOT EXISTS；需已 USE 目标图空间。"""
        self.select_space(space_name)
        tag = self._validate_identifier(tag_name)
        prop_sql = ", ".join(
            f"{self._validate_identifier(k)} {v}" for k, v in properties.items()
        )
        self._execute(f"CREATE TAG IF NOT EXISTS `{tag}`({prop_sql});")
        logger.info("Ensured Nebula tag exists: %s", tag)

    def create_edge_type(self, space_name: str, edge_name: str, properties: dict[str, str]) -> None:
        """CREATE EDGE IF NOT EXISTS；需已 USE 目标图空间。"""
        self.select_space(space_name)
        edge = self._validate_identifier(edge_name)
        prop_sql = ", ".join(
            f"{self._validate_identifier(k)} {v}" for k, v in properties.items()
        )
        self._execute(f"CREATE EDGE IF NOT EXISTS `{edge}`({prop_sql});")
        logger.info("Ensured Nebula edge type exists: %s", edge)

    def close(self) -> None:
        """关闭 Nebula 连接。"""
        if self._session:
            self._session.release()
            self._session = None
        if self._pool:
            self._pool.close()
            self._pool = None
        logger.info("Nebula connection closed")

    def add_nodes(
        self, space_name: str, tag: str, nodes: list[dict], chunk_size: int = 10000
    ) -> int:
        """分块批量插入节点。"""
        self.select_space(space_name)
        validated_tag = self._validate_identifier(tag)
        created_count = 0
        for begin in range(0, len(nodes), chunk_size):
            batch = nodes[begin : begin + chunk_size]
            values_sql: list[str] = []
            for node in batch:
                vid = self._escape_string(str(node["vid"]))
                properties = node.get("properties", {})
                properties_json = self._escape_string(json.dumps(properties, ensure_ascii=False))
                values_sql.append(f'"{vid}": ("{vid}", "{properties_json}")')
            if not values_sql:
                continue
            query = (
                f'INSERT VERTEX `{validated_tag}`(id, properties) '
                f'VALUES {", ".join(values_sql)};'
            )
            self._execute(query)
            created_count += len(batch)
        return created_count

    def add_edges(
        self, space_name: str, edge_type: str, edges: list[dict], chunk_size: int = 1000
    ) -> int:
        """分块批量插入边（关系）。"""
        self.select_space(space_name)
        validated_edge_type = self._validate_identifier(edge_type)
        created_count = 0
        for begin in range(0, len(edges), chunk_size):
            batch = edges[begin : begin + chunk_size]
            values_sql: list[str] = []
            for edge in batch:
                source_vid = self._escape_string(str(edge["source_vid"]))
                target_vid = self._escape_string(str(edge["target_vid"]))
                edge_id = self._escape_string(f"{source_vid} to {target_vid}")
                properties = edge.get("properties", {})
                properties_json = self._escape_string(json.dumps(properties, ensure_ascii=False))
                values_sql.append(
                    f'"{source_vid}"->"{target_vid}"@0: ("{edge_id}", "{properties_json}")'
                )
            if not values_sql:
                continue
            query = (
                f'INSERT EDGE `{validated_edge_type}`(id, properties) '
                f'VALUES {", ".join(values_sql)};'
            )
            self._execute(query)
            created_count += len(batch)
        return created_count

    def delete_nodes(self, space_name: str, vids: list[str], cascade: bool = True) -> int:
        """批量删除节点。"""
        self.select_space(space_name)
        deleted_count = 0
        for vid in vids:
            escaped_vid = self._escape_string(str(vid))
            query = (
                f'DELETE VERTEX "{escaped_vid}" WITH EDGE;'
                if cascade
                else f'DELETE VERTEX "{escaped_vid}";'
            )
            self._execute(query)
            deleted_count += 1
        return deleted_count

    def delete_edges(self, space_name: str, edge_type: str, edges: list[dict]) -> int:
        """按 source_vid/target_vid 批量删除边。"""
        self.select_space(space_name)
        validated_edge_type = self._validate_identifier(edge_type)
        deleted_count = 0
        for edge in edges:
            source_vid = self._escape_string(str(edge["source_vid"]))
            target_vid = self._escape_string(str(edge["target_vid"]))
            self._execute(f'DELETE EDGE `{validated_edge_type}` "{source_vid}"->"{target_vid}"@0;')
            deleted_count += 1
        return deleted_count

    def execute_operation(self, space_name: str, operation: str, data: dict) -> dict:
        """执行数据库操作。"""
        validated_data = self._validate_operation_data(operation, data)
        handlers = {
            "add_nodes": self._handle_add_nodes,
            "add_edges": self._handle_add_edges,
            "delete_nodes": self._handle_delete_nodes,
            "delete_edges": self._handle_delete_edges,
        }
        handler = handlers.get(operation)
        if not handler:
            raise ValueError(f"Unknown operation: {operation}")
        return handler(space_name, validated_data)

    def ping(self) -> bool:
        """通过简单查询验证连接可用"""
        try:
            self._execute("SHOW SPACES;")
            return True
        except Exception:
            return False

    def _handle_add_nodes(self, space_name: str, data: dict) -> dict:
        tag = data["tag"]
        nodes = data["nodes"]
        count = self.add_nodes(space_name, tag, nodes)
        return {"operation": "add_nodes", "count": count, "status": "success"}

    def _handle_add_edges(self, space_name: str, data: dict) -> dict:
        edge_type = data["edge_type"]
        edges = data["edges"]
        count = self.add_edges(space_name, edge_type, edges)
        return {"operation": "add_edges", "count": count, "status": "success"}

    def _handle_delete_nodes(self, space_name: str, data: dict) -> dict:
        vids = data["vids"]
        cascade = data["cascade"]
        count = self.delete_nodes(space_name, vids, cascade)
        return {"operation": "delete_nodes", "count": count, "status": "success"}

    def _handle_delete_edges(self, space_name: str, data: dict) -> dict:
        edge_type = data["edge_type"]
        edges = data["edges"]
        count = self.delete_edges(space_name, edge_type, edges)
        return {"operation": "delete_edges", "count": count, "status": "success"}

    @staticmethod
    def _validate_operation_data(operation: str, data: dict) -> dict:
        model_map = {
            "add_nodes": AddNodesData,
            "add_edges": AddEdgesData,
            "delete_nodes": DeleteNodesData,
            "delete_edges": DeleteEdgesData,
        }
        model_cls = model_map.get(operation)
        if not model_cls:
            raise ValueError(f"Unknown operation: {operation}")
        try:
            return model_cls.model_validate(data).model_dump()
        except ValidationError as exc:
            raise ValueError(f"Invalid payload for operation {operation}: {exc}") from exc

    def _execute(self, query: str):
        if not self._session:
            self.connect()
        result = self._session.execute(query)
        if not result.is_succeeded():
            raise RuntimeError(
                f"Nebula query failed: {result.error_msg()} (code={result.error_code()}), query={query}"
            )
        return result

    @staticmethod
    def _validate_identifier(identifier: str) -> str:
        if not identifier or not _IDENTIFIER_PATTERN.match(identifier):
            logger.error(f"Invalid identifier: {identifier!r}")
            raise ValueError(f"Invalid identifier: {identifier!r}")
        return identifier

    @staticmethod
    def _escape_string(value: str) -> str:
        return value.replace("\\", "\\\\").replace('"', '\\"')