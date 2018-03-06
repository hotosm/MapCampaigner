var client = new XMLHttpRequest();
client.open('GET', 'static/RESOURCES.md');
client.onreadystatechange = function() {
    var converter = new showdown.Converter(),
    text      = client.responseText,
    html      = converter.makeHtml(text);
    var page=document.getElementById("markdown-content");
    page.innerHTML=html;
    console.log(html);
}
client.send();