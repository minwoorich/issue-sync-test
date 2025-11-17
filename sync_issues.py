#!/usr/bin/env python3
"""
GitHub Issues를 Notion 데이터베이스로 동기화하는 스크립트
"""

import os
import sys
import re
import json
import yaml
import requests
from datetime import datetime
from typing import List, Dict, Optional, Any
from pathlib import Path


class GitHubNotionSync:
    def __init__(self, repo: str, notion_api_key: str, notion_database_id: str):
        self.repo = repo  # format: "owner/repo"
        self.notion_api_key = notion_api_key
        self.notion_database_id = notion_database_id
        self.github_token = os.environ.get('GITHUB_TOKEN')
        
        self.notion_headers = {
            "Authorization": f"Bearer {self.notion_api_key}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        
        self.github_headers = {
            "Accept": "application/vnd.github.v3+json"
        }
        if self.github_token:
            self.github_headers["Authorization"] = f"token {self.github_token}"

    def get_github_issues(self) -> List[Dict]:
        """GitHub Issues를 가져옵니다"""
        url = f"https://api.github.com/repos/{self.repo}/issues"
        params = {
            "state": "all",  # open, closed, all
            "per_page": 100
        }
        
        try:
            response = requests.get(url, headers=self.github_headers, params=params)
            response.raise_for_status()
            issues = response.json()
            
            # Pull Requests 제외 (Issues API가 PR도 포함함)
            issues = [issue for issue in issues if 'pull_request' not in issue]
            
            print(f"✓ GitHub에서 {len(issues)}개의 이슈를 가져왔습니다.")
            return issues
        except requests.exceptions.RequestException as e:
            print(f"✗ GitHub API 호출 실패: {e}")
            sys.exit(1)

    def get_issue_projects_info(self, issue: Dict) -> Dict[str, Any]:
        """GraphQL로 이슈의 Projects V2 정보를 가져옵니다 (모든 레벨 포함)"""
        issue_number = issue['number']
        node_id = issue.get('node_id')  # Issue의 global node ID
        
        if not node_id:
            print(f"  ⚠ Issue #{issue_number}: node_id 없음")
            return {}
        
        # GraphQL 쿼리 - node_id를 사용하여 모든 레벨의 Projects 조회
        query = """
        query($nodeId: ID!) {
          node(id: $nodeId) {
            ... on Issue {
              projectItems(first: 10) {
                nodes {
                  project {
                    title
                    number
                    owner {
                      ... on User {
                        login
                      }
                      ... on Organization {
                        login
                      }
                    }
                  }
                  fieldValues(first: 20) {
                    nodes {
                      ... on ProjectV2ItemFieldSingleSelectValue {
                        name
                        field {
                          ... on ProjectV2SingleSelectField {
                            name
                          }
                        }
                      }
                      ... on ProjectV2ItemFieldNumberValue {
                        number
                        field {
                          ... on ProjectV2Field {
                            name
                          }
                        }
                      }
                      ... on ProjectV2ItemFieldTextValue {
                        text
                        field {
                          ... on ProjectV2Field {
                            name
                          }
                        }
                      }
                      ... on ProjectV2ItemFieldIterationValue {
                        title
                        field {
                          ... on ProjectV2IterationField {
                            name
                          }
                        }
                      }
                      ... on ProjectV2ItemFieldDateValue {
                        date {
                          start
                          end
                        }
                        field {
                          ... on ProjectV2Field {
                            name
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
        """
        
        variables = {
            "nodeId": node_id
        }
        
        try:
            response = requests.post(
                "https://api.github.com/graphql",
                headers={
                    "Authorization": f"Bearer {self.github_token}",
                    "Content-Type": "application/json"
                },
                json={"query": query, "variables": variables}
            )
            response.raise_for_status()
            data = response.json()
            
            if "errors" in data:
                print(f"  ⚠ GraphQL 에러 (Issue #{issue_number}): {data['errors']}")
                return {}
            
            # 프로젝트 정보 파싱
            return self._parse_projects_data(data)
            
        except requests.exceptions.RequestException as e:
            print(f"  ⚠ Projects 정보 조회 실패 (Issue #{issue_number}): {e}")
            return {}

    def _parse_projects_data(self, data: Dict) -> Dict[str, Any]:
        """GraphQL 응답에서 프로젝트 정보를 파싱합니다"""
        try:
            # node 쿼리 결과에서 직접 가져오기
            issue_data = data.get("data", {}).get("node", {})
            project_items = issue_data.get("projectItems", {}).get("nodes", [])
            
            if not project_items:
                return {}
            
            # 첫 번째 프로젝트 정보만 사용 (이슈가 여러 프로젝트에 속할 수 있지만 단순화)
            first_project = project_items[0]
            project_data = first_project.get("project", {})
            project_owner = project_data.get("owner", {}).get("login", "")
            
            project_info = {
                "project_title": project_data.get("title", ""),
                "project_number": project_data.get("number", None),
                "project_owner": project_owner,
                "fields": {}
            }
            
            # 필드 값들 파싱
            field_values = first_project.get("fieldValues", {}).get("nodes", [])
            for field_value in field_values:
                if not field_value:
                    continue
                
                field_name = None
                field_data = None
                
                # Single Select (Status, Priority 등)
                if "field" in field_value and "name" in field_value:
                    field_obj = field_value.get("field", {})
                    field_name = field_obj.get("name")
                    field_data = field_value.get("name")
                
                # Number (Story Points, Capacity 등)
                elif "number" in field_value:
                    field_obj = field_value.get("field", {})
                    field_name = field_obj.get("name")
                    field_data = field_value.get("number")
                
                # Text
                elif "text" in field_value:
                    field_obj = field_value.get("field", {})
                    field_name = field_obj.get("name")
                    field_data = field_value.get("text")
                
                # Iteration (Sprint)
                elif "title" in field_value:
                    field_obj = field_value.get("field", {})
                    field_name = field_obj.get("name")
                    field_data = field_value.get("title")
                
                # Date (Start date, Target date, Due date 등)
                elif "date" in field_value:
                    field_obj = field_value.get("field", {})
                    field_name = field_obj.get("name")
                    date_value = field_value.get("date", {})
                    field_data = date_value.get("start")  # start 날짜만 사용
                
                if field_name and field_data is not None:
                    project_info["fields"][field_name] = field_data
            
            return project_info
            
        except (KeyError, TypeError, AttributeError) as e:
            print(f"  ⚠ Projects 데이터 파싱 실패: {e}")
            return {}

    def convert_body_to_blocks(self, body: str) -> List[Dict]:
        """이슈 본문(Markdown)을 Notion 블록으로 변환합니다"""
        if not body or body.strip() == "":
            return [{
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{
                        "type": "text",
                        "text": {"content": "(내용 없음)"}
                    }]
                }
            }]
        
        blocks = []
        lines = body.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # 코드 블록 처리 (```)
            if line.strip().startswith('```'):
                code_block, lines_consumed = self._parse_code_block(lines[i:])
                blocks.append(code_block)
                i += lines_consumed
                continue
            
            # 헤딩 처리 (# ## ###)
            heading_match = re.match(r'^(#{1,3})\s+(.+)$', line)
            if heading_match:
                level = len(heading_match.group(1))
                text = heading_match.group(2)
                blocks.append(self._create_heading_block(level, text))
                i += 1
                continue
            
            # 인용구 처리 (>)
            if line.strip().startswith('>'):
                text = line.strip()[1:].strip()
                blocks.append(self._create_quote_block(text))
                i += 1
                continue
            
            # 불릿 리스트 처리 (-, *)
            bullet_match = re.match(r'^[\s]*[-*]\s+(.+)$', line)
            if bullet_match:
                text = bullet_match.group(1)
                blocks.append(self._create_bullet_list_block(text))
                i += 1
                continue
            
            # 번호 리스트 처리 (1. 2. 3.)
            number_match = re.match(r'^[\s]*\d+\.\s+(.+)$', line)
            if number_match:
                text = number_match.group(1)
                blocks.append(self._create_numbered_list_block(text))
                i += 1
                continue
            
            # 체크박스 리스트 처리 (- [ ] or - [x])
            checkbox_match = re.match(r'^[\s]*[-*]\s+\[([ xX])\]\s+(.+)$', line)
            if checkbox_match:
                checked = checkbox_match.group(1).lower() == 'x'
                text = checkbox_match.group(2)
                blocks.append(self._create_todo_block(text, checked))
                i += 1
                continue
            
            # 일반 paragraph (rich text 포함)
            if line.strip():
                blocks.append(self._create_paragraph_block(line))
            else:
                # 빈 줄
                blocks.append(self._create_paragraph_block(""))
            
            i += 1
        
        return blocks

    def _parse_code_block(self, lines: List[str]) -> tuple:
        """코드 블록 파싱 (``` ~ ```)"""
        first_line = lines[0].strip()
        language = first_line[3:].strip() or "plain text"
        
        code_lines = []
        i = 1
        while i < len(lines):
            if lines[i].strip() == '```':
                break
            code_lines.append(lines[i])
            i += 1
        
        code_content = '\n'.join(code_lines)
        
        block = {
            "object": "block",
            "type": "code",
            "code": {
                "rich_text": [{
                    "type": "text",
                    "text": {"content": code_content[:2000]}  # Notion 제한
                }],
                "language": self._map_language(language)
            }
        }
        
        return block, i + 1

    def _map_language(self, lang: str) -> str:
        """GitHub 언어를 Notion 언어로 매핑"""
        lang_map = {
            "js": "javascript",
            "ts": "typescript",
            "py": "python",
            "rb": "ruby",
            "sh": "shell",
            "bash": "shell",
            "yml": "yaml",
            "": "plain text"
        }
        return lang_map.get(lang.lower(), lang.lower())

    def _create_heading_block(self, level: int, text: str) -> Dict:
        """헤딩 블록 생성"""
        heading_type = f"heading_{level}"
        return {
            "object": "block",
            "type": heading_type,
            heading_type: {
                "rich_text": self._parse_rich_text(text)
            }
        }

    def _create_quote_block(self, text: str) -> Dict:
        """인용구 블록 생성"""
        return {
            "object": "block",
            "type": "quote",
            "quote": {
                "rich_text": self._parse_rich_text(text)
            }
        }

    def _create_bullet_list_block(self, text: str) -> Dict:
        """불릿 리스트 블록 생성"""
        return {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": self._parse_rich_text(text)
            }
        }

    def _create_numbered_list_block(self, text: str) -> Dict:
        """번호 리스트 블록 생성"""
        return {
            "object": "block",
            "type": "numbered_list_item",
            "numbered_list_item": {
                "rich_text": self._parse_rich_text(text)
            }
        }

    def _create_todo_block(self, text: str, checked: bool) -> Dict:
        """체크박스 블록 생성"""
        return {
            "object": "block",
            "type": "to_do",
            "to_do": {
                "rich_text": self._parse_rich_text(text),
                "checked": checked
            }
        }

    def _create_paragraph_block(self, text: str) -> Dict:
        """일반 paragraph 블록 생성"""
        return {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": self._parse_rich_text(text) if text.strip() else []
            }
        }

    def _parse_rich_text(self, text: str) -> List[Dict]:
        """Markdown 인라인 스타일을 Notion rich text로 변환"""
        # 간단한 구현: 일단 plain text로
        # TODO: 굵은 글씨(**), 이탤릭(*), 인라인 코드(`), 링크([]()), 등 처리 가능
        
        if not text or len(text) == 0:
            return []
        
        # 텍스트가 너무 길면 잘라냄 (Notion 제한)
        if len(text) > 2000:
            text = text[:1997] + "..."
        
        rich_text_parts = []
        
        # 인라인 코드 처리 (`)
        parts = re.split(r'(`[^`]+`)', text)
        for part in parts:
            if not part:
                continue
            
            if part.startswith('`') and part.endswith('`'):
                # 인라인 코드
                rich_text_parts.append({
                    "type": "text",
                    "text": {"content": part[1:-1]},
                    "annotations": {"code": True}
                })
            else:
                # 굵은 글씨, 이탤릭 등 처리
                rich_text_parts.extend(self._parse_bold_italic(part))
        
        return rich_text_parts if rich_text_parts else [{
            "type": "text",
            "text": {"content": text}
        }]

    def _parse_bold_italic(self, text: str) -> List[Dict]:
        """굵은 글씨(**) 와 이탤릭(*) 처리"""
        if not text:
            return []
        
        # 굵은 글씨 + 이탤릭 (***) 
        bold_italic_pattern = r'\*\*\*([^\*]+)\*\*\*'
        # 굵은 글씨 (**)
        bold_pattern = r'\*\*([^\*]+)\*\*'
        # 이탤릭 (*)
        italic_pattern = r'\*([^\*]+)\*'
        
        # 복잡한 파싱 대신 간단하게 처리
        # 실제로는 재귀적으로 파싱해야 하지만, 기본 케이스만 처리
        
        parts = []
        remaining = text
        
        # 굵은 글씨 찾기
        for match in re.finditer(bold_pattern, remaining):
            start, end = match.span()
            
            # 앞부분 일반 텍스트
            if start > 0:
                before = remaining[:start]
                if before:
                    parts.append({
                        "type": "text",
                        "text": {"content": before}
                    })
            
            # 굵은 글씨 부분
            parts.append({
                "type": "text",
                "text": {"content": match.group(1)},
                "annotations": {"bold": True}
            })
            
            remaining = remaining[end:]
        
        # 남은 텍스트
        if remaining and not parts:
            # 굵은 글씨가 없었다면 그냥 일반 텍스트로
            parts.append({
                "type": "text",
                "text": {"content": text}
            })
        elif remaining:
            parts.append({
                "type": "text",
                "text": {"content": remaining}
            })
        
        return parts if parts else [{
            "type": "text",
            "text": {"content": text}
        }]

    def search_notion_page_by_issue_number(self, issue_number: int, repository: str) -> Optional[str]:
        """Notion에서 이슈 번호 + 레포지토리로 페이지를 검색합니다"""
        url = f"https://api.notion.com/v1/databases/{self.notion_database_id}/query"
        
        # Issue Number AND Repository로 검색 (중복 방지)
        data = {
            "filter": {
                "and": [
                    {
                        "property": "Issue Number",
                        "number": {
                            "equals": issue_number
                        }
                    },
                    {
                        "property": "Repository",
                        "rich_text": {
                            "equals": repository
                        }
                    }
                ]
            }
        }
        
        try:
            response = requests.post(url, headers=self.notion_headers, json=data)
            response.raise_for_status()
            results = response.json().get("results", [])
            
            if results:
                return results[0]["id"]
            return None
        except requests.exceptions.RequestException as e:
            print(f"✗ Notion 검색 실패 ({repository} Issue #{issue_number}): {e}")
            return None

    def create_notion_page(self, issue: Dict) -> bool:
        """Notion에 새 페이지를 생성합니다"""
        url = "https://api.notion.com/v1/pages"
        
        # 라벨 처리
        labels = [label["name"] for label in issue.get("labels", [])]
        labels_text = ", ".join(labels) if labels else "없음"
        
        # 상태 매핑
        status = "Open" if issue["state"] == "open" else "Closed"
        
        data = {
            "parent": {"database_id": self.notion_database_id},
            "properties": {
                "Title": {
                    "title": [
                        {
                            "text": {
                                "content": issue["title"]
                            }
                        }
                    ]
                },
                "Issue Number": {
                    "number": issue["number"]
                },
                "Status": {
                    "select": {
                        "name": status
                    }
                },
                "Labels": {
                    "rich_text": [
                        {
                            "text": {
                                "content": labels_text
                            }
                        }
                    ]
                },
                "URL": {
                    "url": issue["html_url"]
                },
                "Created At": {
                    "date": {
                        "start": issue["created_at"]
                    }
                }
            }
        }
        
        # Assignee 추가 (있는 경우)
        if issue.get("assignee"):
            data["properties"]["Assignee"] = {
                "rich_text": [
                    {
                        "text": {
                            "content": issue["assignee"]["login"]
                        }
                    }
                ]
            }
        
        # Milestone 추가 (있는 경우)
        if issue.get("milestone"):
            data["properties"]["Milestone"] = {
                "rich_text": [
                    {
                        "text": {
                            "content": issue["milestone"]["title"]
                        }
                    }
                ]
            }
        
        # Repository 추가 (여러 레포 지원 시 유용)
        data["properties"]["Repository"] = {
            "rich_text": [
                {
                    "text": {
                        "content": self.repo
                    }
                }
            ]
        }
        
        # Projects V2 정보 조회 및 추가
        projects_info = self.get_issue_projects_info(issue)
        if projects_info:
            # Project 이름
            if projects_info.get("project_title"):
                data["properties"]["Project"] = {
                    "rich_text": [
                        {
                            "text": {
                                "content": projects_info["project_title"]
                            }
                        }
                    ]
                }
            
            # Projects 필드들
            fields = projects_info.get("fields", {})
            
            # Status (Backlog, Ready, In progress, In review, Done)
            if "Status" in fields:
                data["properties"]["Project Status"] = {
                    "select": {
                        "name": fields["Status"]
                    }
                }
            
            # Priority
            if "Priority" in fields:
                data["properties"]["Priority"] = {
                    "select": {
                        "name": fields["Priority"]
                    }
                }
            
            # Story Points (Number)
            if "Story Points" in fields:
                data["properties"]["Story Points"] = {
                    "number": fields["Story Points"]
                }
            
            # Capacity (Number)
            if "Capacity" in fields:
                data["properties"]["Capacity"] = {
                    "number": fields["Capacity"]
                }
            
            # Sprint (Iteration)
            if "Sprint" in fields:
                data["properties"]["Sprint"] = {
                    "rich_text": [
                        {
                            "text": {
                                "content": str(fields["Sprint"])
                            }
                        }
                    ]
                }
            
            # Date 필드들 (Start date, Target date, Due date 등)
            # Date 타입 필드는 자동으로 감지하여 추가
            date_field_names = ["Start date", "Target date", "Due date", "Start Date", "Target Date", "Due Date"]
            for date_field in date_field_names:
                if date_field in fields:
                    data["properties"][date_field] = {
                        "date": {
                            "start": fields[date_field]
                        }
                    }
        
        # 이슈 본문을 페이지 콘텐츠로 추가
        issue_body = issue.get("body", "")
        data["children"] = self.convert_body_to_blocks(issue_body)
        
        try:
            response = requests.post(url, headers=self.notion_headers, json=data)
            response.raise_for_status()
            print(f"  ✓ Issue #{issue['number']} 생성 완료: {issue['title']}")
            return True
        except requests.exceptions.RequestException as e:
            print(f"  ✗ Issue #{issue['number']} 생성 실패: {e}")
            if hasattr(e.response, 'text'):
                print(f"    에러 상세: {e.response.text}")
            return False

    def update_notion_page(self, page_id: str, issue: Dict) -> bool:
        """Notion 페이지를 업데이트합니다"""
        url = f"https://api.notion.com/v1/pages/{page_id}"
        
        # 라벨 처리
        labels = [label["name"] for label in issue.get("labels", [])]
        labels_text = ", ".join(labels) if labels else "없음"
        
        # 상태 매핑
        status = "Open" if issue["state"] == "open" else "Closed"
        
        data = {
            "properties": {
                "Title": {
                    "title": [
                        {
                            "text": {
                                "content": issue["title"]
                            }
                        }
                    ]
                },
                "Status": {
                    "select": {
                        "name": status
                    }
                },
                "Labels": {
                    "rich_text": [
                        {
                            "text": {
                                "content": labels_text
                            }
                        }
                    ]
                },
                "URL": {
                    "url": issue["html_url"]
                }
            }
        }
        
        # Assignee 업데이트 (있는 경우)
        if issue.get("assignee"):
            data["properties"]["Assignee"] = {
                "rich_text": [
                    {
                        "text": {
                            "content": issue["assignee"]["login"]
                        }
                    }
                ]
            }
        
        # Milestone 업데이트 (있는 경우)
        if issue.get("milestone"):
            data["properties"]["Milestone"] = {
                "rich_text": [
                    {
                        "text": {
                            "content": issue["milestone"]["title"]
                        }
                    }
                ]
            }
        
        # Repository 업데이트
        data["properties"]["Repository"] = {
            "rich_text": [
                {
                    "text": {
                        "content": self.repo
                    }
                }
            ]
        }
        
        # Projects V2 정보 업데이트
        projects_info = self.get_issue_projects_info(issue)
        if projects_info:
            # Project 이름
            if projects_info.get("project_title"):
                data["properties"]["Project"] = {
                    "rich_text": [
                        {
                            "text": {
                                "content": projects_info["project_title"]
                            }
                        }
                    ]
                }
            
            # Projects 필드들
            fields = projects_info.get("fields", {})
            
            # Status (Backlog, Ready, In progress, In review, Done)
            if "Status" in fields:
                data["properties"]["Project Status"] = {
                    "select": {
                        "name": fields["Status"]
                    }
                }
            
            # Priority
            if "Priority" in fields:
                data["properties"]["Priority"] = {
                    "select": {
                        "name": fields["Priority"]
                    }
                }
            
            # Size
            if "Size" in fields:
                data["properties"]["Size"] = {
                    "select": {
                        "name": fields["Size"]
                    }
                }
            
            # Story Points (Number)
            if "Story Points" in fields:
                data["properties"]["Story Points"] = {
                    "number": fields["Story Points"]
                }
            
            # Capacity (Number)
            if "Capacity" in fields:
                data["properties"]["Capacity"] = {
                    "number": fields["Capacity"]
                }
            
            # Sprint (Iteration)
            sprint_field_names = ["Sprint", "Iteration"]
            for sprint_field in sprint_field_names:
                if sprint_field in fields:
                    data["properties"]["Sprint"] = {
                        "rich_text": [
                            {
                                "text": {
                                    "content": str(fields[sprint_field])
                                }
                            }
                        ]
                    }
            
            # Date 필드들 (Start date, Target date, Due date 등)
            # Date 타입 필드는 자동으로 감지하여 추가
            date_field_names = ["Start date", "Target date", "Due date", "Start Date", "Target Date", "Due Date"]
            for date_field in date_field_names:
                if date_field in fields:
                    data["properties"][date_field] = {
                        "date": {
                            "start": fields[date_field]
                        }
                    }
        
        try:
            # 1. 페이지 속성 업데이트
            response = requests.patch(url, headers=self.notion_headers, json=data)
            response.raise_for_status()
            
            # 2. 페이지 본문(블록) 업데이트
            self.update_page_content(page_id, issue)
            
            print(f"  ✓ Issue #{issue['number']} 업데이트 완료: {issue['title']}")
            return True
        except requests.exceptions.RequestException as e:
            print(f"  ✗ Issue #{issue['number']} 업데이트 실패: {e}")
            if hasattr(e.response, 'text'):
                print(f"    에러 상세: {e.response.text}")
            return False

    def update_page_content(self, page_id: str, issue: Dict):
        """페이지 본문(블록)을 업데이트합니다"""
        try:
            # 1. 기존 블록 가져오기
            blocks_url = f"https://api.notion.com/v1/blocks/{page_id}/children"
            response = requests.get(blocks_url, headers=self.notion_headers)
            response.raise_for_status()
            existing_blocks = response.json().get("results", [])
            
            # 2. 기존 블록 삭제
            for block in existing_blocks:
                delete_url = f"https://api.notion.com/v1/blocks/{block['id']}"
                requests.delete(delete_url, headers=self.notion_headers)
            
            # 3. 새 블록 추가
            issue_body = issue.get("body", "")
            new_blocks = self.convert_body_to_blocks(issue_body)
            
            append_data = {"children": new_blocks}
            response = requests.patch(blocks_url, headers=self.notion_headers, json=append_data)
            response.raise_for_status()
            
        except requests.exceptions.RequestException as e:
            print(f"    ⚠ 본문 업데이트 실패 (속성은 업데이트됨): {e}")

    def sync(self):
        """GitHub Issues를 Notion으로 동기화합니다"""
        print("=" * 60)
        print("GitHub → Notion 이슈 동기화 시작")
        print("=" * 60)
        print(f"Repository: {self.repo}")
        print(f"Notion Database ID: {self.notion_database_id[:8]}...")
        print()
        
        # GitHub Issues 가져오기
        issues = self.get_github_issues()
        
        if not issues:
            print("동기화할 이슈가 없습니다.")
            return
        
        print(f"\n동기화 진행 중...")
        print("-" * 60)
        
        created_count = 0
        updated_count = 0
        failed_count = 0
        
        for issue in issues:
            # Notion에 이미 존재하는지 확인 (Issue Number + Repository)
            page_id = self.search_notion_page_by_issue_number(issue["number"], self.repo)
            
            if page_id:
                # 업데이트
                if self.update_notion_page(page_id, issue):
                    updated_count += 1
                else:
                    failed_count += 1
            else:
                # 새로 생성
                if self.create_notion_page(issue):
                    created_count += 1
                else:
                    failed_count += 1
        
        # 결과 출력
        print()
        print("=" * 60)
        print("동기화 완료!")
        print("=" * 60)
        print(f"생성됨: {created_count}개")
        print(f"업데이트됨: {updated_count}개")
        print(f"실패: {failed_count}개")
        print(f"총 처리: {len(issues)}개")
        print("=" * 60)


def load_config() -> Optional[Dict]:
    """config.yml 파일을 로드합니다 (선택사항)"""
    config_path = Path(__file__).parent / 'config.yml'
    
    if not config_path.exists():
        return None
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        print(f"⚠ config.yml 로드 실패: {e}")
        print("기본 모드(현재 레포만)로 계속합니다...")
        return None


def get_repositories_to_sync(config: Optional[Dict]) -> List[str]:
    """동기화할 레포 목록을 반환합니다"""
    if config and 'repositories' in config and config['repositories']:
        repos = config['repositories']
        print(f"📋 config.yml에서 {len(repos)}개 레포를 찾았습니다.")
        return repos
    
    # config가 없으면 현재 레포만
    current_repo = os.environ.get('GITHUB_REPOSITORY')
    if not current_repo:
        print("✗ GITHUB_REPOSITORY 환경 변수가 설정되지 않았습니다.")
        print("  config.yml이 없으면 GITHUB_REPOSITORY가 필요합니다.")
        sys.exit(1)
    
    print(f"📋 현재 레포만 동기화: {current_repo}")
    return [current_repo]


def setup_github_token(config: Optional[Dict]) -> str:
    """GitHub Token을 설정합니다"""
    # config에서 PAT 사용 여부 확인
    use_pat = config.get('use_personal_access_token', False) if config else False
    
    if use_pat:
        # workflow에서 GITHUB_PAT: ${{ secrets.PAT_GITHUB }}로 설정됨
        token = os.environ.get('GITHUB_PAT')
        if token:
            print("🔑 PAT 사용 (여러 레포 + Projects 접근 가능)")
            return token
        else:
            print("⚠ PAT가 설정되지 않았습니다. GITHUB_TOKEN 사용...")
    
    # 기본: GITHUB_TOKEN 사용
    token = os.environ.get('GITHUB_TOKEN')
    if token:
        print("🔑 GITHUB_TOKEN 사용 (기본)")
        return token
    
    print("✗ GitHub Token이 없습니다 (GITHUB_TOKEN 또는 PAT 필요)")
    sys.exit(1)


def main():
    print("=" * 70)
    print("GitHub Issues → Notion 동기화 시작")
    print("=" * 70)
    print()
    
    # 1. 필수 환경 변수 확인
    notion_api_key = os.environ.get('NOTION_API_KEY')
    notion_database_id = os.environ.get('NOTION_DATABASE_ID')
    
    if not notion_api_key:
        print("✗ NOTION_API_KEY 환경 변수가 설정되지 않았습니다.")
        sys.exit(1)
    
    if not notion_database_id:
        print("✗ NOTION_DATABASE_ID 환경 변수가 설정되지 않았습니다.")
        sys.exit(1)
    
    # 2. config.yml 로드 (선택사항)
    print("⚙️  설정 로드 중...")
    config = load_config()
    
    if config:
        print("✓ config.yml 발견!")
    else:
        print("ℹ️  config.yml 없음 - 기본 모드(현재 레포만)")
    print()
    
    # 3. GitHub Token 설정
    github_token = setup_github_token(config)
    os.environ['GITHUB_TOKEN'] = github_token  # 전역 설정
    
    # 4. 동기화할 레포 목록
    repositories = get_repositories_to_sync(config)
    print()
    
    # 5. 각 레포 동기화
    total_created = 0
    total_updated = 0
    total_failed = 0
    total_issues = 0
    
    for idx, repo in enumerate(repositories, 1):
        print("=" * 70)
        print(f"[{idx}/{len(repositories)}] 레포: {repo}")
        print("=" * 70)
        
        try:
            # GitHubNotionSync 인스턴스 생성
            syncer = GitHubNotionSync(repo, notion_api_key, notion_database_id)
            
            # 동기화 실행
            syncer.sync()
            
            # 통계 수집 (간단하게 sync 메서드에서 반환하도록 수정 가능)
            # 지금은 각 레포마다 출력만 함
            
        except Exception as e:
            print(f"✗ 레포 {repo} 동기화 실패: {e}")
            import traceback
            traceback.print_exc()
            continue
        
        print()
    
    # 6. 전체 요약
    print()
    print("=" * 70)
    print("🎉 전체 동기화 완료!")
    print("=" * 70)
    print(f"동기화한 레포: {len(repositories)}개")
    for repo in repositories:
        print(f"  - {repo}")
    print("=" * 70)


if __name__ == "__main__":
    main()

