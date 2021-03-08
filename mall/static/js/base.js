var vm = new Vue({
    el: '.header_con',
    // 修改Vue变量的读取语法，避免和django模板语法冲突
    delimiters: ['[[', ']]'],
    data: {
        username: '',
    },
    mounted(){
        // 获取cookie中的用户名
    	this.username = getCookie('username');
    }
});