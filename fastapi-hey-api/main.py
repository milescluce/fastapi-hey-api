from fastapi import FastAPI
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Any
from pathlib import Path
import json
from contextlib import asynccontextmanager

type HeyAPIOutputDir = str
"""The cwd where the HeyAPIOutputFolder will be generated."""
type HeyAPIOutputFolderName = str | None
"""The name of the folder with the openapi.json, and hey-api Typescript sdk will land. 
This will attempt to make it dynamically based on FastAPI.title of the app. If you have two FastAPI apps 
with the same name, this will cause them to overwrite each other."""

HEY_API_CONFIG_TEMPLATE = """
import { defineConfig } from '@hey-api/openapi-ts';

export default defineConfig({
  input: {input},
  output: {output},
});
"""


class HeyAPIConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".hey-api.env",
        env_prefix='HEY_API_CONFIG'
    )
    output_dir: HeyAPIOutputDir = "."
    output_folder_name: HeyAPIOutputFolderName = None

    def get_folder_name(self, app: FastAPI) -> HeyAPIOutputFolderName:
        output_folder_name = self.output_folder_name if self.output_folder_name else app.title
        return output_folder_name
   
    @property
    def output_path(self) -> Path:
        p = Path(self.output_path)
        assert p.is_dir()
        p.touch(exist_ok=True)
        return p

    def scaffold(self, oas: OpenAPISchema):
        op = self.output_path
        p = op / "openapi-ts.config.ts"
        p.touch()
        gi = op / ".gitignore"
        gi.touch()
        gi.write_text("openapi.json")
        oap = op / "openapi.json"
        oap.touch()
        json.dump(fp=oap, obj=oas) #type: ignore
        tmpl = HEY_API_CONFIG_TEMPLATE.format(
            input = str(oap),
            output = f"{str(self.output_path)}/client"
        )
        p.write_text(tmpl)

type OpenAPISchema = dict[str, Any]
"""This is representation of the OpenAPI schema in memory that will be written to a 
.json file wherever .hey-api.env specifies, the default is '.'"""

@asynccontextmanager
def hey_api_lifespan(app: FastAPI):
    config = HeyAPIConfig()
    open_api = app.openapi()
    config.scaffold(open_api)
    yield app

