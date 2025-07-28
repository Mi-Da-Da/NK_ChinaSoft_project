from backend.config.settings import Config
import os
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings.dashscope import DashScopeEmbeddings
from backend.services.ai_service import AIService
from langchain_core.prompts import PromptTemplate
from langchain_core.documents import Document
from typing import List
import time
from pathlib import Path


class AttractionsService:
    """景点服务类"""

    def __init__(self):
        # 配置参数
        persist_directory = "./utils/TouristAttraction_data"
        self.embeddings = DashScopeEmbeddings(
            model="text-embedding-v1",
            dashscope_api_key=Config.TONGYI_API_KEY
        )
        self.db = Chroma(
            persist_directory=persist_directory,
            embedding_function=self.embeddings
        )
        self.ai_service = AIService()  # 统一大模型调用
        self.prompt = PromptTemplate.from_template(
            """
            你是一个专业的旅游顾问，使用以下上下文信息回答用户关于旅游景点的问题。
            回答要简洁、专业，并包含实用的旅游建议。

            {context}

            用户问题：{question}

            请给出有帮助的回答：
            """
        )
    def query(self, question: str):
        """对外主接口：输入问题，返回答案和相关文档"""
        start_time = time.time()
        if not question:
            return {"error": "问题不能为空"}
        try:
            # 检索
            retrieved_docs = self.db.similarity_search(question, k=5)
            docs_content = "\n\n".join(doc.page_content for doc in retrieved_docs)
            prompt = self.prompt.format(question=question, context=docs_content)
            answer = self.ai_service.invoke_ai(prompt)
            source_list = []
            for doc in retrieved_docs:
                source_name = doc.metadata.get("source", "未知来源")
                page = doc.metadata.get("page", "")
                source_info = source_name
                if page:
                    source_info += f" (第{page}页)"
                source_list.append({
                    "source": source_info,
                    "content": doc.page_content[:200] + "..."
                })
            elapsed = time.time() - start_time
            return {
                "answer": answer,
                "sources": source_list,
                "response_time": f"{elapsed:.2f}秒",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
        except Exception as e:
            return {"error": f"处理请求时出错: {str(e)}"}