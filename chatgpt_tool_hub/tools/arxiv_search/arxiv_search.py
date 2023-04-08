from chatgpt_tool_hub.tools.arxiv_search.wrapper import ArxivAPIWrapper
from chatgpt_tool_hub.tools.base_tool import BaseTool


class ArxivTool(BaseTool):
    """ a tool to call arxiv api: """

    name = "arxiv"
    description = (
        "Useful for when you need to answer questions about scientific research or search for papers "
        "Like: which papers has a certain author published? what are some papers in a specific field? "
        "Input should be a search_query in english. There is not any quotation marks in any search_query"
        
        "In the tool, each paper is divided up into a number of fields that can individually be searched. "
        "A field consists of field prefix, a colon, and search term. Fields can be combined by a boolean operator. "
        
        "`field prefix` only can be: `ti` (Title), `au` (Author), `abs` (Abstract) and `co` (Comment). "
        "`boolean operator` only can be: `AND`, `OR`, `ANDNOT`. "
        
        "Example: if we wanted all of the articles by the author Adrian DelMaestro "
        "with titles that did not contain the computer vision. "
        "A search_query should be au:del_maestro+ANDNOT+ti:computer+vision. "
    )
    api_wrapper: ArxivAPIWrapper

    def _run(self, query: str) -> str:
        """Use the Arxiv tool."""
        return self.api_wrapper.run(query)

    async def _arun(self, query: str) -> str:
        """Use the Arxiv tool asynchronously."""
        raise NotImplementedError("ArxivTool does not support async")


if __name__ == "__main__":
    tool = ArxivTool(api_wrapper=ArxivAPIWrapper())
    content = tool.run("au:Adam Coates")
    print(content)
