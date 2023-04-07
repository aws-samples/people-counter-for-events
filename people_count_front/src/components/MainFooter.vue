<!-- Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. -->
<!-- SPDX-License-Identifier:MIT-0 -->

<template>
    <footer class="footer">
        <div class="container">
            <p class="text-muted">
                Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
            </p>
        </div>
    </footer>
</template>
<style>
.footer {
    position: absolute;
    bottom: 0;
    width: 100%;
    /* Set the fixed height of the footer here */
    height: 60px;
    background-color: #f5f5f5;
}
body > .container {
    padding: 60px 15px 0;
}
.container .text-muted {
    margin: 20px 0;
    text-align: auto;
}

.footer > .container {
    padding-right: 15px;
    padding-left: 15px;
}
</style>
