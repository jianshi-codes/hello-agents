from dotenv import load_dotenv
# 加载 .env 文件中的环境变量
load_dotenv()

import os
import ast
import math
import operator
from serpapi import SerpApiClient
from typing import Dict, Any


def search(query: str) -> str:
    """
    一个基于SerpApi的实战网页搜索引擎工具。
    它会智能地解析搜索结果，优先返回直接答案或知识图谱信息。
    """
    print(f"🔍 正在执行 [SerpApi] 网页搜索: {query}")
    try:
        api_key = os.getenv("SERPAPI_API_KEY")
        if not api_key:
            return "错误：SERPAPI_API_KEY 未在 .env 文件中配置。"

        params = {
            "engine": "google",
            "q": query,
            "api_key": api_key,
            "gl": "cn",  # 国家代码
            "hl": "zh-cn", # 语言代码
        }
        
        client = SerpApiClient(params)
        results = client.get_dict()
        
        # 智能解析：优先寻找最直接的答案
        if "answer_box_list" in results:
            return "\n".join(results["answer_box_list"])
        if "answer_box" in results and "answer" in results["answer_box"]:
            return results["answer_box"]["answer"]
        if "knowledge_graph" in results and "description" in results["knowledge_graph"]:
            return results["knowledge_graph"]["description"]
        if "organic_results" in results and results["organic_results"]:
            # 如果没有直接答案，则返回前三个有机结果的摘要
            snippets = [
                f"[{i+1}] {res.get('title', '')}\n{res.get('snippet', '')}"
                for i, res in enumerate(results["organic_results"][:3])
            ]
            return "\n\n".join(snippets)
        
        return f"对不起，没有找到关于 '{query}' 的信息。"

    except Exception as e:
        return f"搜索时发生错误: {e}"
    

def calculate(expression: str) -> str:
    """
    A safe calculator function.

    Supported:
    - +, -, *, /, //, %, **
    - parentheses
    - unary + and -
    - math functions: sqrt, sin, cos, tan, log, log10, abs, round
    - constants: pi, e

    Examples:
        calculate("1 + 2 * 3") -> "7"
        calculate("sqrt(16) + sin(pi / 2)") -> "5.0"
    """

    allowed_binary_operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
    }

    allowed_unary_operators = {
        ast.UAdd: operator.pos,
        ast.USub: operator.neg,
    }

    allowed_functions = {
        "sqrt": math.sqrt,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "log": math.log,
        "log10": math.log10,
        "abs": abs,
        "round": round,
    }

    allowed_constants = {
        "pi": math.pi,
        "e": math.e,
    }

    def evaluate(node):
        if isinstance(node, ast.Expression):
            return evaluate(node.body)

        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError("Only numbers are allowed.")

        if isinstance(node, ast.BinOp):
            operator_type = type(node.op)

            if operator_type not in allowed_binary_operators:
                raise ValueError("Unsupported operator.")

            left = evaluate(node.left)
            right = evaluate(node.right)

            return allowed_binary_operators[operator_type](left, right)

        if isinstance(node, ast.UnaryOp):
            operator_type = type(node.op)

            if operator_type not in allowed_unary_operators:
                raise ValueError("Unsupported unary operator.")

            operand = evaluate(node.operand)

            return allowed_unary_operators[operator_type](operand)

        if isinstance(node, ast.Name):
            if node.id in allowed_constants:
                return allowed_constants[node.id]
            raise ValueError(f"Unknown variable or constant: {node.id}")

        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise ValueError("Only simple function calls are allowed.")

            function_name = node.func.id

            if function_name not in allowed_functions:
                raise ValueError(f"Unsupported function: {function_name}")

            args = [evaluate(arg) for arg in node.args]

            return allowed_functions[function_name](*args)

        raise ValueError("Unsupported expression.")

    try:
        expression = expression.replace("×", "*").replace("÷", "/")
        parsed_expression = ast.parse(expression, mode="eval")
        result = evaluate(parsed_expression)

        if not isinstance(result, (int, float)):
            raise ValueError("Result is not a number.")

        return str(result)

    except ZeroDivisionError:
        return "计算时发生错误: Cannot divide by zero."
    except SyntaxError:
        return "计算时发生错误: Invalid expression."
    except Exception as e:
        return f"计算时发生错误: {e}"


class ToolExecutor:
    """
    一个工具执行器，负责管理和执行工具。
    """
    def __init__(self):
        self.tools: Dict[str, Dict[str, Any]] = {}

    def registerTool(self, name: str, description: str, func: callable):
        """
        向工具箱中注册一个新工具。
        """
        if name in self.tools:
            print(f"警告：工具 '{name}' 已存在，将被覆盖。")
        
        self.tools[name] = {"description": description, "func": func}
        print(f"工具 '{name}' 已注册。")

    def getTool(self, name: str) -> callable:
        """
        根据名称获取一个工具的执行函数。
        """
        return self.tools.get(name, {}).get("func")

    def getAvailableTools(self) -> str:
        """
        获取所有可用工具的格式化描述字符串。
        """
        return "\n".join([
            f"- {name}: {info['description']}" 
            for name, info in self.tools.items()
        ])


# --- 工具初始化与使用示例 ---
if __name__ == '__main__':
    # 1. 初始化工具执行器
    toolExecutor = ToolExecutor()

    # 2. 注册我们的实战搜索工具
    search_description = "一个网页搜索引擎。当你需要回答关于时事、事实以及在你的知识库中找不到的信息时，应使用此工具。"
    toolExecutor.registerTool("Search", search_description, search)

    calculate_description = """一个计算器工具。当你需要计算一个 String 格式类型的计算表达式时，应使用此工具。

此工具支持:
- +, -, *, /, //, %, **
- parentheses
- unary + and -
- math functions: sqrt, sin, cos, tan, log, log10, abs, round
- constants: pi, e
"""
    toolExecutor.registerTool("Calculator", calculate_description, calculate)
    
    # 3. 打印可用的工具
    print("\n--- 可用的工具 ---")
    print(toolExecutor.getAvailableTools())

    # 4. 智能体的Action调用，这次我们问一个实时性的问题
    print("\n--- 执行 Action: Search['英伟达最新的GPU型号是什么'] ---")
    tool_name = "Search"
    tool_input = "英伟达最新的GPU型号是什么"

    tool_function = toolExecutor.getTool(tool_name)
    if tool_function:
        observation = tool_function(tool_input)
        print("--- 观察 (Observation) ---")
        print(observation)
    else:
        print(f"错误：未找到名为 '{tool_name}' 的工具。")

    print("\n--- 执行 Action: Calculator['(123 + 456) × 789 / 12'] ---")
    tool_name = "Calculator"
    tool_input = "(123 + 456) * 789/ 12"

    tool_function = toolExecutor.getTool(tool_name)
    if tool_function:
        observation = tool_function(tool_input)
        print("--- 观察 (Observation) ---")
        print(observation)
    else:
        print(f"错误：未找到名为 '{tool_name}' 的工具。")
