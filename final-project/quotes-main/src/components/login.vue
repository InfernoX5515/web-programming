<template>
    <h1>Please Login</h1>
    <form>
        <table>
            <tr>
                <td>
                    <label for="User">User</label>
                </td>
                <td>
                    <input type="text" id="user" name="user" v-model="user" />
                </td>
            </tr>
            <tr>
                <td>
                    <label for="password">Password</label>
                </td>
                <td>
                    <input type="text" id="password" name="password" v-model="password" />
                </td>
            </tr>
        </table>
        <button type="button" @click="handleAddSubmit">Submit</button>
        <br>
        <a href="/">Cancel</a>
    </form>
    <a href="http://localhost:5000/register">Not registered? Sign up now!</a>
  </template>
  
  <script>
  import axios from 'axios';
  
  export default {
  data() {
    return {
      user: '',
      password: ''
    };
  },
  methods: {
    login(payload) {
      const path = 'http://localhost:5000/login';
      axios.post(path, payload)
        .catch((error) => {

          console.log(error);
        });
    },
    handleAddSubmit() {
      const payload = {
        user: this.user,
        password: this.password
      };
      this.login(payload);
      this.initForm();
    },
    initForm() {
      this.user = '';
      this.password = '';
    },
  }
};
  </script>