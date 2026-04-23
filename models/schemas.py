from typing import Literal
from pydantic import BaseModel, Field

from datetime import datetime

class NodeItem(BaseModel):

    vid: str = Field(..., description="节点唯一标识")
    properties: dict = Field(default_factory=dict, description="节点属性")


class AddNodesData(BaseModel):

    tag: str = Field(..., description="节点类型，如Character")
    nodes: list[NodeItem] = Field(..., description="节点列表")


class EdgeItem(BaseModel):

    source_vid: str = Field(..., description="源节点vid")
    target_vid: str = Field(..., description="目标节点vid")
    properties: dict = Field(default_factory=dict, description="边属性")


class AddEdgesData(BaseModel):

    edge_type: str = Field(..., description="边类型，如Character_to_Character")
    edges: list[EdgeItem] = Field(..., description="边列表")

class EdgeItemSimple(BaseModel):

    source_vid: str = Field(..., description="源节点vid")
    target_vid: str = Field(..., description="目标节点vid")


class DeleteNodesData(BaseModel):

    vids: list[str] = Field(..., description="要删除的节点vid列表")
    cascade: bool = Field(default=True, description="是否级联删除关联边")


class DeleteEdgesData(BaseModel):

    edge_type: str = Field(..., description="边类型，如Character_to_Character")
    edges: list[EdgeItemSimple] = Field(..., description="边列表")


class MessageRequest(BaseModel):

    operation: Literal["add_nodes", "add_edges", "delete_nodes", "delete_edges"]
    data: dict = Field(..., description="根据operation类型的数据")


class MessageResponse(BaseModel):

    success: bool
    message_id: str
    message: str
    timestamp: datetime