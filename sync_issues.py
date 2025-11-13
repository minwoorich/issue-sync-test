#!/usr/bin/env python3
"""
GitHub Issues를 Notion 데이터베이스로 동기화하는 스크립트
"""

import os
import sys
import requests
from datetime import datetime
from typing import List, Dict, Optional


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

    def convert_body_to_blocks(self, body: str) -> List[Dict]:
        """이슈 본문을 Notion 블록으로 변환합니다"""
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
        
        for line in lines:
            # 빈 줄도 paragraph로 추가 (Notion에서 줄바꿈 표현)
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{
                        "type": "text",
                        "text": {"content": line}
                    }] if line.strip() else []
                }
            })
        
        return blocks

    def search_notion_page_by_issue_number(self, issue_number: int) -> Optional[str]:
        """Notion에서 이슈 번호로 페이지를 검색합니다"""
        url = f"https://api.notion.com/v1/databases/{self.notion_database_id}/query"
        
        data = {
            "filter": {
                "property": "Issue Number",
                "number": {
                    "equals": issue_number
                }
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
            print(f"✗ Notion 검색 실패 (Issue #{issue_number}): {e}")
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
            # Notion에 이미 존재하는지 확인
            page_id = self.search_notion_page_by_issue_number(issue["number"])
            
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


def main():
    # 환경 변수 확인
    repo = os.environ.get('GITHUB_REPOSITORY')
    notion_api_key = os.environ.get('NOTION_API_KEY')
    notion_database_id = os.environ.get('NOTION_DATABASE_ID')
    
    if not repo:
        print("✗ GITHUB_REPOSITORY 환경 변수가 설정되지 않았습니다.")
        sys.exit(1)
    
    if not notion_api_key:
        print("✗ NOTION_API_KEY 환경 변수가 설정되지 않았습니다.")
        sys.exit(1)
    
    if not notion_database_id:
        print("✗ NOTION_DATABASE_ID 환경 변수가 설정되지 않았습니다.")
        sys.exit(1)
    
    # 동기화 실행
    syncer = GitHubNotionSync(repo, notion_api_key, notion_database_id)
    syncer.sync()


if __name__ == "__main__":
    main()

