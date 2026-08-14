const button = document.querySelector("#run-demo");
const result = document.querySelector("#result");

button.addEventListener("click", async () => {
  button.disabled = true;
  result.textContent = "正在整理材料和岗位要求…";

  try {
    const response = await fetch("/api/v1/demo/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ task_id: "demo-s001", human_approved: false }),
    });
    const data = await response.json();
    result.textContent = `证据匹配度 ${data.match.match_score} 分；材料覆盖度 ${data.match.evidence_coverage}%。${data.match.disclaimer}`;
  } catch (error) {
    result.textContent = "暂时无法生成报告，请保留材料后重试。";
  } finally {
    button.disabled = false;
  }
});
