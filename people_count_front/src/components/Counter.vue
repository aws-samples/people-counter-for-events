<!-- Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved. -->
<!-- SPDX-License-Identifier:MIT-0 -->

<template>
    <div class="">
        <div class="card-header main p-3 pt-2">
            <div class="pt-1">
                <p class="mb-0 text-capitalize main-title" style="text-align: center">
                    来場者カウント
                </p>
                <!--architecture説明カード-->

                <div class="card top-card">
                    <div class="p-3 pt-0 text-center card-body">
                        <div class="row first-row">
                            <div class="total-count-arr">
                                <h4 class="total-count-title">総来場者数</h4>
                                <h4 class="total-count-val">{{ totalCount }}人</h4>
                            </div>
                            <div class="currunt-count-arr">
                                <h4 class="currunt-count-title">現在の来場者数</h4>
                                <h4 class="currunt-count-val">{{ curruntCount }}人</h4>
                            </div>
                        </div>
                        <div class="row second-row">
                            <div class="comapny-time-arr">
                                <h5 class="comapny-time time-string">
                                    {{ time }}
                                </h5>
                                <h4 class="comapny-time-title">時点の集計結果</h4>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import { API, graphqlOperation } from "@aws-amplify/api";
import config from "../aws-exports";
import { onUpdatevideostream } from "../graphql/subscriptions";
import { getvideostream } from "../graphql/queries";
import { ref, onMounted } from "vue";
import moment from "moment";

API.configure(config);

export default {
    name: "MainCounter",
    setup() {
        let curruntCount = ref(0);
        let totalCount = ref(0);
        let time = ref(null);

        /**
         * return curunt time
         */
        const getCount = () => {
            API.graphql({ query: getvideostream, variables: { video_stream_id: "0" } })
                .then(async (result) => {
                    console.log(result.data.getvideostream);
                    curruntCount.value = result.data.getvideostream.current_count;
                    totalCount.value = result.data.getvideostream.total_count;
                })
                .catch((error) => {
                    console.log("dynamoError", error);
                });
        };

        /**
         * return curunt time
         */
        const getNow = () => {
            time.value = moment(new Date()).format("MM[月]DD[日], HH:mm:ss");
        };

        /**
         * sbscrive Count(currunt count, total count)
         */
        const subscribeCount = () => {
            try {
                API.graphql(graphqlOperation(onUpdatevideostream)).subscribe({
                    next: (result) => {
                        curruntCount.value = result.value.data.onUpdatevideostream.current_count;
                        totalCount.value = result.value.data.onUpdatevideostream.total_count;
                    },
                });
            } catch (error) {
                console.log("dynamoError", error);
            }
        };

        onMounted(() => {
            //initail count(only use first time)
            getCount();
            //Get currunt time
            getNow();
            //Update currunt time
            setInterval(getNow.bind(this), 1000);
            //Mount subscribe
            subscribeCount();
        });

        return {
            curruntCount,
            totalCount,
            time,
        };
    },
};
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
/* card main css  */
.main {
    margin-top: 1%;
}
/* first row css */
.first-row {
    margin-top: 1%;
    width: 100%;
    font-size: 1px;
}
.time-string {
    font-size: 3rem;
}
.second-row {
    margin-top: 1%;
}
.main-title {
    font-size: 5rem;
}

.comapny-time {
    font-size: 1.2rem;
}
.comapny-time-arr {
    width: 100%;
    margin: auto;
    float: right;
    text-align: center;
}

.comapny-time-title {
    color: purple;
    font-size: 2rem;
}

.currunt-count-val {
    font-size: 10rem;
}
.currunt-count-arr {
    width: 45%;
    margin: auto;
    float: right;
    text-align: center;
}

.currunt-count-title {
    color: sandybrown;
    font-size: 4rem;
}

.total-count-val {
    font-size: 10rem;
}
.total-count-title {
    color: green;
    font-size: 4rem;
}

.total-count-arr {
    width: 45%;
    margin: auto;
    float: right;
    text-align: center;
}

.top-card {
    margin-top: 5%;
}
</style>
