let vm = new Vue({
    el: '#app',
    // 修改Vue变量的读取语法，避免和django模板语法冲突
    delimiters: ['[[', ']]'],
    data: {
        host,
        error_username: false,
        error_pwd: false,
        error_pwd_message: '',
        username: '',
        password: '',
        remembered: false,
    },
    methods: {
        check_username: function () {
            let re = /^[a-zA-Z0-9_-]{5,20}$/;
            if (re.test(this.username)) {
                this.error_username = false;
            } else {
                this.error_username = true;
            }
        },
        check_pwd: function () {
            let re = /^[0-9A-Za-z]{8,20}$/;
            if (re.test(this.password)) {
                this.error_pwd = false;
            } else {
                this.error_pwd = true;
            }
        },
        // 表单提交
        on_submit: function(){
            this.check_username();
            this.check_pwd();

            if (this.error_username === true || this.error_pwd ===true) {
                // 不满足登录条件：禁用表单
				window.event.returnValue = false
            }
        },
    },
})