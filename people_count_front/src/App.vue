<!-- Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. -->
<!-- SPDX-License-Identifier:MIT-0 -->

<template>
    <div id="app">
        <MainHeader />
        <Counter />
        <MainFooter />
    </div>
</template>

<script>
import Counter from "./components/Counter.vue";
import MainHeader from "./components/MainHeader";
import MainFooter from "./components/MainFooter";

export default {
    name: "App",
    components: {
        Counter,
        MainHeader,
        MainFooter,
    },
};
</script>

<style>
#app {
    font-family: Avenir, Helvetica, Arial, sans-serif;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    text-align: center;
    color: #2c3e50;
    /* margin-top: 60px; */
}
</style>
