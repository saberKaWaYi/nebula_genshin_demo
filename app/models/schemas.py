from pydantic import BaseModel, Field
from typing import Literal, Optional
from datetime import datetime


class NodeItem(BaseModel):
    """节点数据项"""
    id: str = Field(..., description="节点唯一标识")
    properties: dict = Field(default_factory=dict, description="节点属性")


class AddNodesData(BaseModel):
    """添加节点数据"""
    label: str = Field(..., description="节点标签，如Character")
    nodes: list[NodeItem] = Field(..., description="节点列表")


class EdgeItem(BaseModel):
    """边数据项"""
    id: str = Field(..., description="边唯一标识")
    source_id: str = Field(..., description="源节点ID")
    target_id: str = Field(..., description="目标节点ID")
    properties: dict = Field(default_factory=dict, description="边属性")


class AddEdgesData(BaseModel):
    """添加边数据"""
    label: str = Field(..., description="关系类型，如KNOWS")
    edges: list[EdgeItem] = Field(..., description="边列表")


class DeleteNodesData(BaseModel):
    """删除节点数据"""
    node_ids: list[str] = Field(..., description="要删除的节点ID列表")
    cascade: bool = Field(default=True, description="是否级联删除关联边")


class DeleteEdgesData(BaseModel):
    """删除边数据"""
    edge_ids: list[str] = Field(..., description="要删除的边ID列表")


class MessageRequest(BaseModel):
    """消息请求"""
    operation: Literal["add_nodes", "add_edges", "delete_nodes", "delete_edges"]
    data: dict = Field(..., description="根据operation类型的数据")


class MessageResponse(BaseModel):
    """消息响应"""
    success: bool
    message_id: str
    message: str
    timestamp: datetime


class ConsumedMessage(BaseModel):
    """已消费的消息"""
    message_id: str
    timestamp: datetime
    operation: str
    data: dict
    status: str


class ConsumeResponse(BaseModel):
    """消费响应"""
    success: bool
    message: Optional[ConsumedMessage] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    neo4j_connected: bool
    rabbitmq_connected: bool